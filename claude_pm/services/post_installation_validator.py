#!/usr/bin/env python3
"""
PostInstallationValidator Service - Claude PM Framework
======================================================

This service provides comprehensive validation and health checks for the
post-installation process. It ensures all components are properly installed
and configured.

Features:
- Component validation
- Health checks
- Error diagnosis
- Recovery suggestions
- Cross-platform compatibility checks
"""

import os
import sys
import json
import time
import platform
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.base_service import BaseService
from ..core.logging_config import setup_logging

console = Console()
logger = setup_logging(__name__)


class ValidationStatus(Enum):
    """Validation status levels."""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


class ValidationSeverity(Enum):
    """Validation severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ValidationCheck:
    """Represents a single validation check."""
    name: str
    description: str
    status: ValidationStatus
    severity: ValidationSeverity
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ValidationSuite:
    """Represents a suite of validation checks."""
    name: str
    description: str
    checks: List[ValidationCheck]
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warned_checks: int = 0
    skipped_checks: int = 0
    execution_time: float = 0.0


class PostInstallationValidator(BaseService):
    """
    Comprehensive validation service for post-installation checks.
    
    This service performs extensive validation of the post-installation
    process including component deployment, configuration, permissions,
    and system compatibility.
    """
    
    def __init__(self, working_dir: Optional[Path] = None):
        super().__init__(name="post_installation_validator")
        self.working_dir = working_dir or Path.cwd()
        self.platform = platform.system().lower()
        self.user_home = Path.home()
        self.global_config_dir = self.user_home / ".claude-pm"
        
        # Validation state
        self.validation_suites: List[ValidationSuite] = []
        self.all_checks: List[ValidationCheck] = []
        
        self.logger = setup_logging(__name__)
    
    async def _initialize(self) -> bool:
        """Initialize the PostInstallationValidator service."""
        try:
            self.logger.info("Initializing PostInstallationValidator service")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize PostInstallationValidator: {e}")
            return False
    
    async def _cleanup(self) -> bool:
        """Cleanup the PostInstallationValidator service."""
        try:
            self.logger.info("PostInstallationValidator cleanup completed")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup PostInstallationValidator: {e}")
            return False
    
    def _create_check(self, name: str, description: str, status: ValidationStatus, 
                     severity: ValidationSeverity, message: str, 
                     details: Optional[Dict[str, Any]] = None, 
                     error: Optional[str] = None) -> ValidationCheck:
        """Create a validation check."""
        return ValidationCheck(
            name=name,
            description=description,
            status=status,
            severity=severity,
            message=message,
            details=details,
            timestamp=datetime.now().isoformat(),
            error=error
        )
    
    def _add_check(self, check: ValidationCheck):
        """Add a validation check to the results."""
        self.all_checks.append(check)
        
        # Log the check result
        if check.status == ValidationStatus.PASS:
            self.logger.info(f"✅ {check.name}: {check.message}")
        elif check.status == ValidationStatus.WARN:
            self.logger.warning(f"⚠️ {check.name}: {check.message}")
        elif check.status == ValidationStatus.FAIL:
            self.logger.error(f"❌ {check.name}: {check.message}")
        else:
            self.logger.info(f"⏭️ {check.name}: {check.message}")
    
    async def validate_directory_structure(self) -> ValidationSuite:
        """Validate the directory structure."""
        start_time = time.time()
        checks = []
        
        # Expected directories
        expected_dirs = {
            "scripts": self.global_config_dir / "scripts",
            "templates": self.global_config_dir / "templates",
            "agents": self.global_config_dir / "agents",
            "framework": self.global_config_dir / "framework",
            "schemas": self.global_config_dir / "schemas",
            "config": self.global_config_dir / "config",
            "cli": self.global_config_dir / "cli",
            "docs": self.global_config_dir / "docs",
            "bin": self.global_config_dir / "bin",
            "memory": self.global_config_dir / "memory",
            "cache": self.global_config_dir / "cache",
            "logs": self.global_config_dir / "logs",
            "index": self.global_config_dir / "index"
        }
        
        # Check global config directory
        if self.global_config_dir.exists():
            check = self._create_check(
                "global_config_dir",
                "Global configuration directory exists",
                ValidationStatus.PASS,
                ValidationSeverity.CRITICAL,
                f"Directory exists: {self.global_config_dir}",
                {"path": str(self.global_config_dir)}
            )
        else:
            check = self._create_check(
                "global_config_dir",
                "Global configuration directory exists",
                ValidationStatus.FAIL,
                ValidationSeverity.CRITICAL,
                f"Directory missing: {self.global_config_dir}",
                {"path": str(self.global_config_dir)}
            )
        checks.append(check)
        self._add_check(check)
        
        # Check expected directories
        for dir_name, dir_path in expected_dirs.items():
            if dir_path.exists():
                check = self._create_check(
                    f"directory_{dir_name}",
                    f"Directory {dir_name} exists",
                    ValidationStatus.PASS,
                    ValidationSeverity.HIGH,
                    f"Directory exists: {dir_path}",
                    {"path": str(dir_path)}
                )
            else:
                check = self._create_check(
                    f"directory_{dir_name}",
                    f"Directory {dir_name} exists",
                    ValidationStatus.FAIL,
                    ValidationSeverity.HIGH,
                    f"Directory missing: {dir_path}",
                    {"path": str(dir_path)}
                )
            checks.append(check)
            self._add_check(check)
        
        # Check permissions
        if self.global_config_dir.exists():
            try:
                # Test write permissions
                test_file = self.global_config_dir / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()
                
                check = self._create_check(
                    "write_permissions",
                    "Write permissions to global config directory",
                    ValidationStatus.PASS,
                    ValidationSeverity.HIGH,
                    "Write permissions verified",
                    {"path": str(self.global_config_dir)}
                )
            except Exception as e:
                check = self._create_check(
                    "write_permissions",
                    "Write permissions to global config directory",
                    ValidationStatus.FAIL,
                    ValidationSeverity.HIGH,
                    f"Write permissions failed: {e}",
                    {"path": str(self.global_config_dir)},
                    error=str(e)
                )
            checks.append(check)
            self._add_check(check)
        
        # Calculate suite statistics
        total_checks = len(checks)
        passed_checks = len([c for c in checks if c.status == ValidationStatus.PASS])
        failed_checks = len([c for c in checks if c.status == ValidationStatus.FAIL])
        warned_checks = len([c for c in checks if c.status == ValidationStatus.WARN])
        skipped_checks = len([c for c in checks if c.status == ValidationStatus.SKIP])
        
        suite = ValidationSuite(
            name="directory_structure",
            description="Directory structure validation",
            checks=checks,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warned_checks=warned_checks,
            skipped_checks=skipped_checks,
            execution_time=time.time() - start_time
        )
        
        self.validation_suites.append(suite)
        return suite
    
    async def validate_component_deployment(self) -> ValidationSuite:
        """Validate component deployment."""
        start_time = time.time()
        checks = []
        
        # Critical components
        critical_components = {
            "framework_core": self.global_config_dir / "framework" / "claude_pm",
            "framework_templates": self.global_config_dir / "framework" / "framework",
            "version_file": self.global_config_dir / "framework" / "VERSION",
            "config_framework": self.global_config_dir / "config" / "framework.json",
            "config_memory": self.global_config_dir / "config" / "memory.json",
            "config_cli": self.global_config_dir / "config" / "cli.json"
        }
        
        for component_name, component_path in critical_components.items():
            if component_path.exists():
                check = self._create_check(
                    f"component_{component_name}",
                    f"Component {component_name} deployed",
                    ValidationStatus.PASS,
                    ValidationSeverity.HIGH,
                    f"Component exists: {component_path}",
                    {"path": str(component_path)}
                )
            else:
                check = self._create_check(
                    f"component_{component_name}",
                    f"Component {component_name} deployed",
                    ValidationStatus.FAIL,
                    ValidationSeverity.HIGH,
                    f"Component missing: {component_path}",
                    {"path": str(component_path)}
                )
            checks.append(check)
            self._add_check(check)
        
        # Check framework core structure
        framework_core = self.global_config_dir / "framework" / "claude_pm"
        if framework_core.exists():
            init_file = framework_core / "__init__.py"
            if init_file.exists():
                check = self._create_check(
                    "framework_core_init",
                    "Framework core __init__.py exists",
                    ValidationStatus.PASS,
                    ValidationSeverity.HIGH,
                    "Framework core properly deployed",
                    {"path": str(init_file)}
                )
            else:
                check = self._create_check(
                    "framework_core_init",
                    "Framework core __init__.py exists",
                    ValidationStatus.FAIL,
                    ValidationSeverity.HIGH,
                    "Framework core missing __init__.py",
                    {"path": str(init_file)}
                )
            checks.append(check)
            self._add_check(check)
        
        # Check configuration files validity
        config_files = {
            "framework.json": self.global_config_dir / "config" / "framework.json",
            "memory.json": self.global_config_dir / "config" / "memory.json",
            "cli.json": self.global_config_dir / "config" / "cli.json"
        }
        
        for config_name, config_path in config_files.items():
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        json.load(f)
                    check = self._create_check(
                        f"config_{config_name}_valid",
                        f"Configuration {config_name} is valid JSON",
                        ValidationStatus.PASS,
                        ValidationSeverity.MEDIUM,
                        f"Configuration file valid: {config_name}",
                        {"path": str(config_path)}
                    )
                except Exception as e:
                    check = self._create_check(
                        f"config_{config_name}_valid",
                        f"Configuration {config_name} is valid JSON",
                        ValidationStatus.FAIL,
                        ValidationSeverity.MEDIUM,
                        f"Configuration file invalid: {config_name}",
                        {"path": str(config_path)},
                        error=str(e)
                    )
                checks.append(check)
                self._add_check(check)
        
        # Calculate suite statistics
        total_checks = len(checks)
        passed_checks = len([c for c in checks if c.status == ValidationStatus.PASS])
        failed_checks = len([c for c in checks if c.status == ValidationStatus.FAIL])
        warned_checks = len([c for c in checks if c.status == ValidationStatus.WARN])
        skipped_checks = len([c for c in checks if c.status == ValidationStatus.SKIP])
        
        suite = ValidationSuite(
            name="component_deployment",
            description="Component deployment validation",
            checks=checks,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warned_checks=warned_checks,
            skipped_checks=skipped_checks,
            execution_time=time.time() - start_time
        )
        
        self.validation_suites.append(suite)
        return suite
    
    async def validate_system_compatibility(self) -> ValidationSuite:
        """Validate system compatibility."""
        start_time = time.time()
        checks = []
        
        # Python version check
        python_version = sys.version_info
        if python_version >= (3, 9):
            check = self._create_check(
                "python_version",
                "Python version compatibility",
                ValidationStatus.PASS,
                ValidationSeverity.CRITICAL,
                f"Python {python_version.major}.{python_version.minor} is supported",
                {"version": f"{python_version.major}.{python_version.minor}"}
            )
        else:
            check = self._create_check(
                "python_version",
                "Python version compatibility",
                ValidationStatus.FAIL,
                ValidationSeverity.CRITICAL,
                f"Python {python_version.major}.{python_version.minor} is not supported (requires 3.9+)",
                {"version": f"{python_version.major}.{python_version.minor}"}
            )
        checks.append(check)
        self._add_check(check)
        
        # Platform compatibility
        supported_platforms = ["darwin", "linux", "windows"]
        if self.platform in supported_platforms:
            check = self._create_check(
                "platform_support",
                "Platform compatibility",
                ValidationStatus.PASS,
                ValidationSeverity.HIGH,
                f"Platform {self.platform} is supported",
                {"platform": self.platform}
            )
        else:
            check = self._create_check(
                "platform_support",
                "Platform compatibility",
                ValidationStatus.WARN,
                ValidationSeverity.HIGH,
                f"Platform {self.platform} has experimental support",
                {"platform": self.platform}
            )
        checks.append(check)
        self._add_check(check)
        
        # Required Python modules
        required_modules = [
            "rich", "click", "pathlib", "json", "os", "sys", 
            "asyncio", "logging", "datetime", "time"
        ]
        
        for module in required_modules:
            try:
                __import__(module)
                check = self._create_check(
                    f"module_{module}",
                    f"Required module {module} available",
                    ValidationStatus.PASS,
                    ValidationSeverity.MEDIUM,
                    f"Module {module} imported successfully",
                    {"module": module}
                )
            except ImportError as e:
                check = self._create_check(
                    f"module_{module}",
                    f"Required module {module} available",
                    ValidationStatus.FAIL,
                    ValidationSeverity.MEDIUM,
                    f"Module {module} not available",
                    {"module": module},
                    error=str(e)
                )
            checks.append(check)
            self._add_check(check)
        
        # Check disk space
        try:
            stat = os.statvfs(self.global_config_dir.parent)
            free_space = stat.f_bavail * stat.f_frsize
            free_space_mb = free_space / (1024 * 1024)
            
            if free_space_mb > 100:  # 100MB minimum
                check = self._create_check(
                    "disk_space",
                    "Sufficient disk space available",
                    ValidationStatus.PASS,
                    ValidationSeverity.MEDIUM,
                    f"Available space: {free_space_mb:.1f}MB",
                    {"free_space_mb": free_space_mb}
                )
            else:
                check = self._create_check(
                    "disk_space",
                    "Sufficient disk space available",
                    ValidationStatus.WARN,
                    ValidationSeverity.MEDIUM,
                    f"Low disk space: {free_space_mb:.1f}MB",
                    {"free_space_mb": free_space_mb}
                )
            checks.append(check)
            self._add_check(check)
        except Exception as e:
            check = self._create_check(
                "disk_space",
                "Sufficient disk space available",
                ValidationStatus.SKIP,
                ValidationSeverity.MEDIUM,
                f"Could not check disk space: {e}",
                error=str(e)
            )
            checks.append(check)
            self._add_check(check)
        
        # Calculate suite statistics
        total_checks = len(checks)
        passed_checks = len([c for c in checks if c.status == ValidationStatus.PASS])
        failed_checks = len([c for c in checks if c.status == ValidationStatus.FAIL])
        warned_checks = len([c for c in checks if c.status == ValidationStatus.WARN])
        skipped_checks = len([c for c in checks if c.status == ValidationStatus.SKIP])
        
        suite = ValidationSuite(
            name="system_compatibility",
            description="System compatibility validation",
            checks=checks,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warned_checks=warned_checks,
            skipped_checks=skipped_checks,
            execution_time=time.time() - start_time
        )
        
        self.validation_suites.append(suite)
        return suite
    
    async def validate_cli_functionality(self) -> ValidationSuite:
        """Validate CLI functionality."""
        start_time = time.time()
        checks = []
        
        # Check if Python module can be imported
        try:
            import importlib.util
            
            # Try to import the CLI module
            cli_module_path = self.global_config_dir / "framework" / "claude_pm" / "cli" / "__init__.py"
            if cli_module_path.exists():
                spec = importlib.util.spec_from_file_location("claude_pm.cli", cli_module_path)
                if spec and spec.loader:
                    check = self._create_check(
                        "cli_module_import",
                        "CLI module can be imported",
                        ValidationStatus.PASS,
                        ValidationSeverity.HIGH,
                        "CLI module import successful",
                        {"module_path": str(cli_module_path)}
                    )
                else:
                    check = self._create_check(
                        "cli_module_import",
                        "CLI module can be imported",
                        ValidationStatus.FAIL,
                        ValidationSeverity.HIGH,
                        "CLI module import failed",
                        {"module_path": str(cli_module_path)}
                    )
            else:
                check = self._create_check(
                    "cli_module_import",
                    "CLI module can be imported",
                    ValidationStatus.FAIL,
                    ValidationSeverity.HIGH,
                    "CLI module file missing",
                    {"module_path": str(cli_module_path)}
                )
            checks.append(check)
            self._add_check(check)
        except Exception as e:
            check = self._create_check(
                "cli_module_import",
                "CLI module can be imported",
                ValidationStatus.FAIL,
                ValidationSeverity.HIGH,
                f"CLI module import error: {e}",
                error=str(e)
            )
            checks.append(check)
            self._add_check(check)
        
        # Check CLI configuration
        cli_config_path = self.global_config_dir / "config" / "cli.json"
        if cli_config_path.exists():
            try:
                with open(cli_config_path, 'r') as f:
                    cli_config = json.load(f)
                
                # Check for required configuration keys
                required_keys = ["default_commands", "shortcuts"]
                for key in required_keys:
                    if key in cli_config:
                        check = self._create_check(
                            f"cli_config_{key}",
                            f"CLI configuration has {key}",
                            ValidationStatus.PASS,
                            ValidationSeverity.MEDIUM,
                            f"CLI configuration key {key} present",
                            {"key": key}
                        )
                    else:
                        check = self._create_check(
                            f"cli_config_{key}",
                            f"CLI configuration has {key}",
                            ValidationStatus.WARN,
                            ValidationSeverity.MEDIUM,
                            f"CLI configuration key {key} missing",
                            {"key": key}
                        )
                    checks.append(check)
                    self._add_check(check)
            except Exception as e:
                check = self._create_check(
                    "cli_config_valid",
                    "CLI configuration is valid",
                    ValidationStatus.FAIL,
                    ValidationSeverity.MEDIUM,
                    f"CLI configuration invalid: {e}",
                    {"path": str(cli_config_path)},
                    error=str(e)
                )
                checks.append(check)
                self._add_check(check)
        
        # Calculate suite statistics
        total_checks = len(checks)
        passed_checks = len([c for c in checks if c.status == ValidationStatus.PASS])
        failed_checks = len([c for c in checks if c.status == ValidationStatus.FAIL])
        warned_checks = len([c for c in checks if c.status == ValidationStatus.WARN])
        skipped_checks = len([c for c in checks if c.status == ValidationStatus.SKIP])
        
        suite = ValidationSuite(
            name="cli_functionality",
            description="CLI functionality validation",
            checks=checks,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warned_checks=warned_checks,
            skipped_checks=skipped_checks,
            execution_time=time.time() - start_time
        )
        
        self.validation_suites.append(suite)
        return suite
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation of post-installation."""
        start_time = time.time()
        
        console.print("[bold blue]🔍 Running Comprehensive Post-Installation Validation[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Run validation suites
            dir_task = progress.add_task("Validating directory structure...", total=1)
            await self.validate_directory_structure()
            progress.update(dir_task, completed=1)
            
            comp_task = progress.add_task("Validating component deployment...", total=1)
            await self.validate_component_deployment()
            progress.update(comp_task, completed=1)
            
            sys_task = progress.add_task("Validating system compatibility...", total=1)
            await self.validate_system_compatibility()
            progress.update(sys_task, completed=1)
            
            cli_task = progress.add_task("Validating CLI functionality...", total=1)
            await self.validate_cli_functionality()
            progress.update(cli_task, completed=1)
        
        # Calculate overall statistics
        total_checks = len(self.all_checks)
        passed_checks = len([c for c in self.all_checks if c.status == ValidationStatus.PASS])
        failed_checks = len([c for c in self.all_checks if c.status == ValidationStatus.FAIL])
        warned_checks = len([c for c in self.all_checks if c.status == ValidationStatus.WARN])
        skipped_checks = len([c for c in self.all_checks if c.status == ValidationStatus.SKIP])
        
        critical_failures = len([c for c in self.all_checks 
                               if c.status == ValidationStatus.FAIL and c.severity == ValidationSeverity.CRITICAL])
        
        # Determine overall status
        if critical_failures > 0:
            overall_status = "critical_failure"
        elif failed_checks > 0:
            overall_status = "failure"
        elif warned_checks > 0:
            overall_status = "warning"
        else:
            overall_status = "success"
        
        results = {
            "overall_status": overall_status,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "warned_checks": warned_checks,
            "skipped_checks": skipped_checks,
            "critical_failures": critical_failures,
            "execution_time": time.time() - start_time,
            "suites": [asdict(suite) for suite in self.validation_suites],
            "all_checks": [asdict(check) for check in self.all_checks],
            "timestamp": datetime.now().isoformat()
        }
        
        return results
    
    async def display_validation_report(self, results: Dict[str, Any]):
        """Display comprehensive validation report."""
        console.print("\n" + "=" * 70)
        console.print("🔍 [bold blue]Post-Installation Validation Report[/bold blue]")
        console.print("=" * 70)
        
        # Overall summary
        status = results["overall_status"]
        status_icon = {
            "success": "✅",
            "warning": "⚠️",
            "failure": "❌",
            "critical_failure": "🚨"
        }.get(status, "❓")
        
        console.print(f"\n{status_icon} [bold]Overall Status:[/bold] {status.upper()}")
        console.print(f"⏱️  [bold]Execution Time:[/bold] {results['execution_time']:.2f} seconds")
        console.print(f"📊 [bold]Total Checks:[/bold] {results['total_checks']}")
        
        # Statistics table
        stats_table = Table(title="Validation Statistics")
        stats_table.add_column("Status", style="cyan")
        stats_table.add_column("Count", justify="right", style="green")
        stats_table.add_column("Percentage", justify="right", style="yellow")
        
        total = results["total_checks"]
        stats_table.add_row("Passed", str(results["passed_checks"]), f"{(results['passed_checks']/total*100):.1f}%")
        stats_table.add_row("Failed", str(results["failed_checks"]), f"{(results['failed_checks']/total*100):.1f}%")
        stats_table.add_row("Warned", str(results["warned_checks"]), f"{(results['warned_checks']/total*100):.1f}%")
        stats_table.add_row("Skipped", str(results["skipped_checks"]), f"{(results['skipped_checks']/total*100):.1f}%")
        
        console.print(stats_table)
        
        # Suite summaries
        console.print(f"\n📋 [bold]Validation Suites:[/bold]")
        for suite in results["suites"]:
            suite_status = "✅" if suite["failed_checks"] == 0 else "❌"
            console.print(f"   {suite_status} {suite['name']}: {suite['passed_checks']}/{suite['total_checks']} passed")
        
        # Show failures and warnings
        failures = [c for c in results["all_checks"] if c["status"] == "fail"]
        warnings = [c for c in results["all_checks"] if c["status"] == "warn"]
        
        if failures:
            console.print(f"\n❌ [bold red]Failures ({len(failures)}):[/bold red]")
            for failure in failures:
                severity_icon = {"critical": "🚨", "high": "🔴", "medium": "🟡", "low": "🟢"}.get(failure["severity"], "")
                console.print(f"   {severity_icon} {failure['name']}: {failure['message']}")
        
        if warnings:
            console.print(f"\n⚠️  [bold yellow]Warnings ({len(warnings)}):[/bold yellow]")
            for warning in warnings:
                console.print(f"   • {warning['name']}: {warning['message']}")
        
        # Recommendations
        console.print(f"\n💡 [bold]Recommendations:[/bold]")
        if results["critical_failures"] > 0:
            console.print("   • Critical failures detected - post-installation may not work correctly")
            console.print("   • Run 'claude-pm init --postinstall-only --force' to retry installation")
        elif results["failed_checks"] > 0:
            console.print("   • Some checks failed - functionality may be limited")
            console.print("   • Review failed checks above and fix issues")
        elif results["warned_checks"] > 0:
            console.print("   • Some warnings detected - installation mostly successful")
            console.print("   • Review warnings above for potential improvements")
        else:
            console.print("   • All checks passed - post-installation successful!")
            console.print("   • Run 'claude-pm health' to verify overall system health")
        
        console.print("=" * 70)
    
    async def save_validation_report(self, results: Dict[str, Any]) -> str:
        """Save validation report to file."""
        try:
            # Create logs directory if it doesn't exist
            logs_dir = self.global_config_dir / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Save detailed JSON report (with enum serialization)
            report_file = logs_dir / f"post_installation_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Convert enums to strings for JSON serialization
            def convert_enums(obj):
                if isinstance(obj, dict):
                    return {k: convert_enums(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_enums(item) for item in obj]
                elif hasattr(obj, 'value'):  # Enum
                    return obj.value
                return obj
            
            serializable_results = convert_enums(results)
            
            with open(report_file, 'w') as f:
                json.dump(serializable_results, f, indent=2)
            
            return str(report_file)
        except Exception as e:
            self.logger.error(f"Failed to save validation report: {e}")
            return ""