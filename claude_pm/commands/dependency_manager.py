"""
Dependency Manager Commands - CLI commands for dependency management and validation

This module provides CLI commands for:
- Dependency checking and validation
- Requirements management
- Package version verification
- Dependency conflict resolution

Created: 2025-07-16 (Emergency restoration)
Purpose: Restore missing claude_pm.commands.dependency_manager import
"""

import click
import json
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any
from claude_pm.utils.subprocess_manager import SubprocessManager

@click.group()
def dependency_manager():
    """Dependency management and validation commands"""
    pass

@dependency_manager.command()
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--check-imports', '-i', is_flag=True, help='Test actual imports')
def check(format, check_imports):
    """Check all dependencies and their versions"""
    
    def _run_command(cmd):
        """Run a command and return output"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return False, "", str(e)
    
    def _check_package_import(package_name):
        """Check if a package can be imported"""
        try:
            spec = importlib.util.find_spec(package_name)
            if spec is not None:
                return True, "importable"
            else:
                return False, "not found"
        except Exception as e:
            return False, str(e)
    
    results = {
        'python_version': sys.version,
        'dependencies': {},
        'claude_pm_modules': {},
        'import_tests': {},
        'errors': [],
        'warnings': []
    }
    
    # Check Python version
    click.echo("🐍 Checking Python version...")
    results['python_version'] = sys.version
    
    # Check pip packages
    click.echo("📦 Checking installed packages...")
    success, pip_list, error = _run_command("pip list --format=json")
    
    if success:
        try:
            packages = json.loads(pip_list)
            for package in packages:
                results['dependencies'][package['name']] = package['version']
        except json.JSONDecodeError:
            results['errors'].append("Failed to parse pip list output")
    else:
        results['errors'].append(f"Failed to get pip list: {error}")
    
    # Check claude-pm specific modules
    click.echo("🔧 Checking claude-pm modules...")
    claude_pm_modules = [
        'claude_pm',
        'claude_pm.core',
        'claude_pm.core.agent_registry',
        'claude_pm.core.unified_core_service',
        'claude_pm.services',
        'claude_pm.services.agent_registry',
        'claude_pm.services.health_monitor',
        'claude_pm.services.shared_prompt_cache',
        'claude_pm.commands',
        'claude_pm.commands.health_commands',
        'claude_pm.commands.dependency_manager'
    ]
    
    for module_name in claude_pm_modules:
        can_import, import_result = _check_package_import(module_name)
        results['claude_pm_modules'][module_name] = {
            'importable': can_import,
            'result': import_result
        }
        
        if not can_import:
            results['errors'].append(f"Cannot import {module_name}: {import_result}")
    
    # Import tests if requested
    if check_imports:
        click.echo("🧪 Testing imports...")
        test_imports = [
            ('click', 'import click'),
            ('asyncio', 'import asyncio'),
            ('pathlib', 'from pathlib import Path'),
            ('typing', 'from typing import Dict, List, Optional'),
            ('dataclasses', 'from dataclasses import dataclass'),
            ('claude_pm', 'import claude_pm'),
            ('agent_registry', 'from claude_pm.core.agent_registry import AgentRegistry'),
            ('unified_core', 'from claude_pm.core.unified_core_service import get_unified_core_service')
        ]
        
        for test_name, import_statement in test_imports:
            try:
                exec(import_statement)
                results['import_tests'][test_name] = {'success': True, 'error': None}
            except Exception as e:
                results['import_tests'][test_name] = {'success': False, 'error': str(e)}
                results['errors'].append(f"Import test failed for {test_name}: {e}")
    
    # Output results
    if format == 'json':
        click.echo(json.dumps(results, indent=2))
    else:
        # Text format output
        if results['errors']:
            click.echo(click.style(f"❌ Found {len(results['errors'])} errors:", fg='red'))
            for error in results['errors']:
                click.echo(f"  • {error}")
        else:
            click.echo(click.style("✅ All dependency checks passed!", fg='green'))
        
        # Show package count
        click.echo(f"\n📦 Installed packages: {len(results['dependencies'])}")
        
        # Show claude-pm module status
        claude_pm_ok = sum(1 for m in results['claude_pm_modules'].values() if m['importable'])
        claude_pm_total = len(results['claude_pm_modules'])
        click.echo(f"🔧 Claude-PM modules: {claude_pm_ok}/{claude_pm_total} importable")
        
        # Show import test results
        if results['import_tests']:
            import_ok = sum(1 for t in results['import_tests'].values() if t['success'])
            import_total = len(results['import_tests'])
            click.echo(f"🧪 Import tests: {import_ok}/{import_total} passed")

@dependency_manager.command()
@click.option('--output', '-o', help='Output file for requirements')
def freeze(output):
    """Generate requirements.txt from current environment"""
    
    def _run_pip_freeze():
        try:
            result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout
            else:
                return None
        except Exception:
            return None
    
    requirements = _run_pip_freeze()
    
    if requirements is None:
        click.echo(click.style("❌ Failed to generate requirements", fg='red'))
        return
    
    if output:
        try:
            with open(output, 'w') as f:
                f.write(requirements)
            click.echo(f"✅ Requirements saved to {output}")
        except Exception as e:
            click.echo(click.style(f"❌ Failed to save requirements: {e}", fg='red'))
    else:
        click.echo("📦 Current requirements:")
        click.echo(requirements)

@dependency_manager.command()
@click.argument('requirements_file', type=click.Path(exists=True))
@click.option('--dry-run', '-n', is_flag=True, help='Show what would be installed without actually installing')
def install(requirements_file, dry_run):
    """Install dependencies from requirements file"""
    
    click.echo(f"📦 Installing dependencies from {requirements_file}")
    
    cmd = ['pip', 'install', '-r', requirements_file]
    if dry_run:
        cmd.append('--dry-run')
        click.echo("🔍 Dry run mode - no packages will be installed")
    
    try:
        manager = SubprocessManager()
        result = manager.run(cmd, capture_output=True, text=True)
        
        if result.success:
            if dry_run:
                click.echo("✅ Dry run completed successfully")
            else:
                click.echo("✅ Dependencies installed successfully")
            
            if result.stdout:
                click.echo(result.stdout)
        else:
            click.echo(click.style("❌ Installation failed", fg='red'))
            if result.stderr:
                click.echo(result.stderr)
    
    except Exception as e:
        click.echo(click.style(f"❌ Installation error: {e}", fg='red'))

@dependency_manager.command()
@click.option('--package', '-p', help='Check specific package')
@click.option('--all', '-a', is_flag=True, help='Check all installed packages')
def outdated(package, all):
    """Check for outdated packages"""
    
    def _run_pip_outdated():
        try:
            cmd = ['pip', 'list', '--outdated', '--format=json']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return None
        except Exception:
            return None
    
    if package:
        # Check specific package
        def _check_package_version(pkg_name):
            try:
                result = subprocess.run(['pip', 'show', pkg_name], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if line.startswith('Version:'):
                            return line.split(':')[1].strip()
                return None
            except Exception:
                return None
        
        current_version = _check_package_version(package)
        if current_version:
            click.echo(f"📦 {package}: {current_version}")
        else:
            click.echo(click.style(f"❌ Package {package} not found", fg='red'))
    
    elif all:
        # Check all packages
        outdated_packages = _run_pip_outdated()
        
        if outdated_packages is None:
            click.echo(click.style("❌ Failed to check for outdated packages", fg='red'))
            return
        
        if not outdated_packages:
            click.echo(click.style("✅ All packages are up to date!", fg='green'))
            return
        
        click.echo(f"📦 Found {len(outdated_packages)} outdated packages:")
        for package in outdated_packages:
            click.echo(f"  {package['name']}: {package['version']} → {package['latest_version']}")
    
    else:
        # Check claude-pm related packages
        claude_pm_packages = ['click', 'asyncio-mqtt', 'python-dotenv', 'pydantic']
        
        click.echo("🔧 Checking claude-pm related packages...")
        outdated_packages = _run_pip_outdated()
        
        if outdated_packages:
            claude_pm_outdated = [p for p in outdated_packages if p['name'].lower() in [pkg.lower() for pkg in claude_pm_packages]]
            
            if claude_pm_outdated:
                click.echo("📦 Outdated claude-pm related packages:")
                for package in claude_pm_outdated:
                    click.echo(f"  {package['name']}: {package['version']} → {package['latest_version']}")
            else:
                click.echo(click.style("✅ All claude-pm related packages are up to date!", fg='green'))
        else:
            click.echo(click.style("✅ No outdated packages found!", fg='green'))

@dependency_manager.command()
def validate():
    """Validate dependency consistency and detect conflicts"""
    
    def _check_dependency_conflicts():
        try:
            # Use pip check to detect conflicts
            result = subprocess.run(['pip', 'check'], capture_output=True, text=True)
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    click.echo("🔍 Validating dependency consistency...")
    
    # Check for conflicts
    no_conflicts, conflict_output = _check_dependency_conflicts()
    
    if no_conflicts and not conflict_output.strip():
        click.echo(click.style("✅ No dependency conflicts detected!", fg='green'))
    else:
        click.echo(click.style("⚠️  Dependency issues detected:", fg='yellow'))
        if conflict_output.strip():
            click.echo(conflict_output)
    
    # Additional validation
    click.echo("\n🧪 Additional validation checks...")
    
    # Check if we can import key modules
    critical_imports = [
        'claude_pm',
        'claude_pm.core.agent_registry',
        'claude_pm.core.unified_core_service'
    ]
    
    import_failures = []
    for module in critical_imports:
        try:
            __import__(module)
            click.echo(f"  ✅ {module}")
        except ImportError as e:
            click.echo(f"  ❌ {module}: {e}")
            import_failures.append((module, str(e)))
    
    if import_failures:
        click.echo(click.style(f"\n⚠️  {len(import_failures)} critical import failures detected", fg='yellow'))
        return False
    else:
        click.echo(click.style("\n✅ All critical imports working!", fg='green'))
        return True

@dependency_manager.command()
@click.option('--upgrade', '-u', is_flag=True, help='Upgrade packages to latest versions')
def update(upgrade):
    """Update claude-pm related dependencies"""
    
    # Key packages for claude-pm
    key_packages = [
        'click',
        'asyncio',
        'pathlib',
        'typing-extensions',
        'dataclasses'
    ]
    
    if upgrade:
        click.echo("⬆️  Upgrading claude-pm dependencies...")
        
        for package in key_packages:
            click.echo(f"Upgrading {package}...")
            try:
                result = subprocess.run(['pip', 'install', '--upgrade', package], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    click.echo(f"  ✅ {package} upgraded")
                else:
                    click.echo(f"  ❌ {package} upgrade failed: {result.stderr}")
            except Exception as e:
                click.echo(f"  ❌ {package} upgrade error: {e}")
    else:
        # Just check versions
        click.echo("📦 Claude-PM dependency versions:")
        
        for package in key_packages:
            try:
                result = subprocess.run(['pip', 'show', package], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if line.startswith('Version:'):
                            version = line.split(':')[1].strip()
                            click.echo(f"  {package}: {version}")
                            break
                else:
                    click.echo(f"  {package}: not installed")
            except Exception as e:
                click.echo(f"  {package}: error checking version")

# Main CLI group
if __name__ == '__main__':
    dependency_manager()