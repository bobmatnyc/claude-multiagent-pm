# EP-0041 Detailed Execution Guides

**Companion Documents**: 
- EP-0041-ORCHESTRATION-ROADMAP.md (Strategic Overview)
- EP-0041-IMPLEMENTATION-STRATEGY.md (Tactical Framework)
- EP-0041-MONITORING-FRAMEWORK.md (Progress Tracking)

**Framework Version**: 0.6.3  
**Document Date**: 2025-07-14  
**Focus**: Step-by-Step Execution Instructions  

## Overview

This document provides detailed, step-by-step execution guides for each phase of the EP-0041 Codebase Modularization Initiative. Each guide includes specific commands, validation steps, and troubleshooting procedures to ensure systematic and successful implementation.

## Phase 1 Execution Guides

### ISS-0114: CLI Module Architecture (Days 1-3)

#### Pre-Execution Setup
```bash
# Create backup of current CLI module
cp claude_pm/cli.py claude_pm/cli.py.backup.$(date +%Y%m%d_%H%M%S)

# Create modular directory structure
mkdir -p claude_pm/cli/{core,commands,utils}
mkdir -p claude_pm/cli/commands/{agents,project,deployment,health,memory,tickets}

# Establish baseline metrics
echo "Baseline CLI module: $(wc -l claude_pm/cli.py) lines"
python -m pytest tests/ --cov=claude_pm --cov-report=term-missing > baseline_coverage.txt
```

#### Day 1: Foundation Layer Extraction

**Step 1: Extract Base Command Interface**
```bash
# Create base command interface
cat > claude_pm/cli/core/base_command.py << 'EOF'
"""Base command interface for modular CLI architecture."""
import click
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseCommand(ABC):
    """Base class for all CLI commands."""
    
    def __init__(self, service_manager=None):
        self.service_manager = service_manager
        
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the command logic."""
        pass
        
    def validate_input(self, **kwargs) -> bool:
        """Validate command input parameters."""
        return True
        
    def handle_error(self, error: Exception) -> None:
        """Handle command execution errors."""
        click.echo(f"Error: {error}", err=True)
EOF
```

**Step 2: Extract Service Manager**
```bash
# Create service manager for CLI coordination
cat > claude_pm/cli/core/service_manager.py << 'EOF'
"""Service manager for CLI service coordination."""
import asyncio
from typing import Dict, Any, Optional
from claude_pm.core.service_manager import ServiceManager as CoreServiceManager

class CLIServiceManager:
    """Manages service initialization and coordination for CLI."""
    
    def __init__(self):
        self.core_service_manager = CoreServiceManager()
        self._services = {}
        
    async def initialize_services(self) -> bool:
        """Initialize all required services for CLI operations."""
        try:
            await self.core_service_manager.initialize()
            self._services['parent_directory_manager'] = await self.core_service_manager.get_service('parent_directory_manager')
            self._services['template_manager'] = await self.core_service_manager.get_service('template_manager')
            return True
        except Exception as e:
            self.handle_initialization_error(e)
            return False
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get initialized service by name."""
        return self._services.get(service_name)
        
    def handle_initialization_error(self, error: Exception) -> None:
        """Handle service initialization errors."""
        print(f"Service initialization failed: {error}")
EOF
```

**Step 3: Create Context Manager**
```bash
# Create CLI context and configuration management
cat > claude_pm/cli/core/context_manager.py << 'EOF'
"""CLI context and configuration management."""
from pathlib import Path
from typing import Dict, Any, Optional
import json

class CLIContextManager:
    """Manages CLI context and configuration."""
    
    def __init__(self):
        self.context = {}
        self.config_path = Path.home() / '.claude-pm' / 'cli_config.json'
        
    def load_context(self) -> Dict[str, Any]:
        """Load CLI context from configuration."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                self.context = json.load(f)
        return self.context
        
    def save_context(self) -> None:
        """Save current context to configuration."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.context, f, indent=2)
            
    def get_context_value(self, key: str, default: Any = None) -> Any:
        """Get context value by key."""
        return self.context.get(key, default)
        
    def set_context_value(self, key: str, value: Any) -> None:
        """Set context value by key."""
        self.context[key] = value
        self.save_context()
EOF
```

**Validation Step 1:**
```bash
# Test extracted components
python -c "
from claude_pm.cli.core.base_command import BaseCommand
from claude_pm.cli.core.service_manager import CLIServiceManager
from claude_pm.cli.core.context_manager import CLIContextManager
print('✅ Foundation layer extraction successful')
"
```

#### Day 2: Command Modularization

**Step 4: Extract Agent Commands**
```bash
# Create agent command module
cat > claude_pm/cli/commands/agents/agent_commands.py << 'EOF'
"""Agent-related CLI commands."""
import click
from claude_pm.cli.core.base_command import BaseCommand

class AgentCommand(BaseCommand):
    """Base class for agent-related commands."""
    pass

@click.group()
def agents():
    """Agent management commands."""
    pass

@agents.command()
@click.option('--list', 'list_agents', is_flag=True, help='List available agents')
@click.option('--status', help='Show agent status')
def agent(list_agents, status):
    """Manage framework agents."""
    if list_agents:
        click.echo("Available agents: Documentation, Ticketing, Version Control")
    if status:
        click.echo(f"Agent {status} status: Active")
EOF
```

**Step 5: Extract Project Commands**
```bash
# Create project command module
cat > claude_pm/cli/commands/project/project_commands.py << 'EOF'
"""Project management CLI commands."""
import click
from claude_pm.cli.core.base_command import BaseCommand

class ProjectCommand(BaseCommand):
    """Base class for project management commands."""
    pass

@click.group()
def project():
    """Project management commands."""
    pass

@project.command()
@click.option('--name', required=True, help='Project name')
@click.option('--template', help='Project template to use')
def create(name, template):
    """Create new project."""
    click.echo(f"Creating project: {name}")
    if template:
        click.echo(f"Using template: {template}")
EOF
```

**Step 6: Extract Deployment Commands**
```bash
# Create deployment command module
cat > claude_pm/cli/commands/deployment/deployment_commands.py << 'EOF'
"""Deployment and setup CLI commands."""
import click
from claude_pm.cli.core.base_command import BaseCommand

class DeploymentCommand(BaseCommand):
    """Base class for deployment commands."""
    pass

@click.group()
def deployment():
    """Deployment and setup commands."""
    pass

@deployment.command()
@click.option('--target', help='Deployment target directory')
@click.option('--force', is_flag=True, help='Force deployment')
def setup(target, force):
    """Setup framework deployment."""
    click.echo(f"Setting up deployment to: {target or 'current directory'}")
    if force:
        click.echo("Force deployment enabled")
EOF
```

**Validation Step 2:**
```bash
# Test command modules
python -c "
from claude_pm.cli.commands.agents.agent_commands import agents
from claude_pm.cli.commands.project.project_commands import project
from claude_pm.cli.commands.deployment.deployment_commands import deployment
print('✅ Command modularization successful')
"
```

#### Day 3: Integration and Testing

**Step 7: Create New CLI Main Module**
```bash
# Create streamlined CLI main module
cat > claude_pm/cli/main.py << 'EOF'
"""Modular CLI main entry point."""
import click
import asyncio
from claude_pm.cli.core.service_manager import CLIServiceManager
from claude_pm.cli.core.context_manager import CLIContextManager
from claude_pm.cli.commands.agents.agent_commands import agents
from claude_pm.cli.commands.project.project_commands import project
from claude_pm.cli.commands.deployment.deployment_commands import deployment

class ModularCLI:
    """Main CLI coordinator for modular architecture."""
    
    def __init__(self):
        self.service_manager = CLIServiceManager()
        self.context_manager = CLIContextManager()
        
    async def initialize(self):
        """Initialize CLI services and context."""
        self.context_manager.load_context()
        await self.service_manager.initialize_services()

@click.group()
@click.pass_context
def cli(ctx):
    """Claude PM Framework CLI - Modular Architecture."""
    ctx.ensure_object(dict)
    cli_instance = ModularCLI()
    asyncio.run(cli_instance.initialize())
    ctx.obj['cli'] = cli_instance

# Register command groups
cli.add_command(agents)
cli.add_command(project)
cli.add_command(deployment)

if __name__ == '__main__':
    cli()
EOF
```

**Step 8: Update Original CLI Module**
```bash
# Replace original CLI with modular version
mv claude_pm/cli.py claude_pm/cli_original.py.backup
cp claude_pm/cli/main.py claude_pm/cli.py

# Update imports in cli.py
sed -i.bak 's/from claude_pm.cli.main import cli/from claude_pm.cli.main import cli/' claude_pm/cli.py
```

**Final Validation:**
```bash
# Test complete CLI functionality
python -m claude_pm.cli --help
python -m claude_pm.cli agents --help
python -m claude_pm.cli project --help
python -m claude_pm.cli deployment --help

# Measure line count reduction
original_lines=$(wc -l claude_pm/cli_original.py.backup | awk '{print $1}')
new_lines=$(wc -l claude_pm/cli.py | awk '{print $1}')
reduction=$((100 - (new_lines * 100 / original_lines)))
echo "✅ CLI module reduced from $original_lines to $new_lines lines ($reduction% reduction)"

# Run test suite
python -m pytest tests/ --cov=claude_pm.cli
```

### ISS-0115: Parent Directory Manager (Days 4-6) - CRITICAL

#### Pre-Execution Setup (CRITICAL PROTECTION)
```bash
# MANDATORY: Create comprehensive backups
timestamp=$(date +%Y%m%d_%H%M%S)
cp claude_pm/services/parent_directory_manager.py "claude_pm/services/parent_directory_manager.py.backup.$timestamp"

# CRITICAL: Test framework template protection before any changes
python -c "
from claude_pm.services.parent_directory_manager import ParentDirectoryManager
import asyncio
async def test_protection():
    manager = ParentDirectoryManager()
    await manager._initialize()
    # Test framework protection methods
    protection_status = manager._protect_framework_template()
    print(f'Framework protection status: {protection_status}')
asyncio.run(test_protection())
"

# Create service directory structure
mkdir -p claude_pm/services/{deployment,config,protection}
```

#### Day 4: Service Layer Extraction

**Step 1: Extract Framework Deployer**
```bash
# Create framework deployment service
cat > claude_pm/services/deployment/framework_deployer.py << 'EOF'
"""Framework deployment service with template management."""
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
import shutil
import json

class FrameworkDeployer:
    """Handles framework template deployment and validation."""
    
    def __init__(self, backup_manager=None, version_manager=None):
        self.backup_manager = backup_manager
        self.version_manager = version_manager
        self.deployment_config = {}
        
    async def deploy_framework_template(self, target_path: Path, template_data: Dict[str, Any]) -> bool:
        """Deploy framework template to target directory."""
        try:
            # Version check before deployment
            if self.version_manager:
                version_compatible = await self.version_manager.check_compatibility(template_data.get('version'))
                if not version_compatible:
                    return False
            
            # Create backup before deployment
            if self.backup_manager:
                backup_created = await self.backup_manager.create_deployment_backup(target_path)
                if not backup_created:
                    return False
            
            # Deploy template
            await self._perform_template_deployment(target_path, template_data)
            return True
            
        except Exception as e:
            await self._handle_deployment_error(e, target_path)
            return False
    
    async def _perform_template_deployment(self, target_path: Path, template_data: Dict[str, Any]) -> None:
        """Perform the actual template deployment."""
        claude_md_path = target_path / 'CLAUDE.md'
        
        # Write template with variable substitution
        with open(claude_md_path, 'w') as f:
            f.write(template_data.get('content', ''))
            
        # Set proper permissions
        claude_md_path.chmod(0o644)
    
    async def _handle_deployment_error(self, error: Exception, target_path: Path) -> None:
        """Handle deployment errors with recovery."""
        print(f"Deployment error: {error}")
        if self.backup_manager:
            await self.backup_manager.restore_from_backup(target_path)
EOF
```

**Step 2: Extract Backup Manager**
```bash
# Create backup management service
cat > claude_pm/services/deployment/backup_manager.py << 'EOF'
"""Backup management service for framework protection."""
import asyncio
from pathlib import Path
from datetime import datetime
import shutil
from typing import List, Optional, Dict, Any

class BackupManager:
    """Manages backup creation, rotation, and restoration."""
    
    def __init__(self, backup_root: Optional[Path] = None):
        self.backup_root = backup_root or Path.home() / '.claude-pm' / 'framework_backups'
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.max_backups = 5
        
    async def create_deployment_backup(self, target_path: Path) -> bool:
        """Create backup before deployment operations."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            claude_md_path = target_path / 'CLAUDE.md'
            
            if claude_md_path.exists():
                backup_name = f"framework_CLAUDE_md_{timestamp}.backup"
                backup_path = self.backup_root / backup_name
                shutil.copy2(claude_md_path, backup_path)
                
                # Rotate old backups
                await self._rotate_backups()
                return True
            return False
            
        except Exception as e:
            print(f"Backup creation failed: {e}")
            return False
    
    async def restore_from_backup(self, target_path: Path, backup_name: Optional[str] = None) -> bool:
        """Restore from backup (latest if backup_name not specified)."""
        try:
            if backup_name:
                backup_path = self.backup_root / backup_name
            else:
                # Get latest backup
                backups = sorted(self.backup_root.glob("framework_CLAUDE_md_*.backup"))
                if not backups:
                    return False
                backup_path = backups[-1]
            
            if backup_path.exists():
                claude_md_path = target_path / 'CLAUDE.md'
                shutil.copy2(backup_path, claude_md_path)
                return True
            return False
            
        except Exception as e:
            print(f"Backup restoration failed: {e}")
            return False
    
    async def _rotate_backups(self) -> None:
        """Rotate backups to maintain maximum count."""
        backups = sorted(self.backup_root.glob("framework_CLAUDE_md_*.backup"))
        if len(backups) > self.max_backups:
            for backup in backups[:-self.max_backups]:
                backup.unlink()
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups with metadata."""
        backups = []
        for backup_path in sorted(self.backup_root.glob("framework_CLAUDE_md_*.backup")):
            backups.append({
                'name': backup_path.name,
                'path': backup_path,
                'size': backup_path.stat().st_size,
                'created': datetime.fromtimestamp(backup_path.stat().st_mtime)
            })
        return backups
EOF
```

**CRITICAL Validation Step:**
```bash
# Test backup system before proceeding
python -c "
import asyncio
from pathlib import Path
from claude_pm.services.deployment.backup_manager import BackupManager

async def test_backup():
    manager = BackupManager()
    
    # Create test file
    test_path = Path('/tmp/test_claude_pm')
    test_path.mkdir(exist_ok=True)
    test_file = test_path / 'CLAUDE.md'
    test_file.write_text('Test framework template')
    
    # Test backup creation
    backup_success = await manager.create_deployment_backup(test_path)
    print(f'✅ Backup creation: {backup_success}')
    
    # Test backup listing
    backups = manager.list_backups()
    print(f'✅ Backup count: {len(backups)}')
    
    # Cleanup
    import shutil
    shutil.rmtree(test_path)

asyncio.run(test_backup())
"
```

### Additional Phase Execution Guides

#### Phase 2 Execution Templates

**ISS-0119: Logging Infrastructure Standardization**
```bash
# Create unified logging system
mkdir -p claude_pm/core/logging/{config,specialized}

# Extract current logging patterns
grep -r "import logging" claude_pm/ > current_logging_patterns.txt
grep -r "logger =" claude_pm/ >> current_logging_patterns.txt
echo "Found $(wc -l current_logging_patterns.txt) logging patterns to consolidate"

# Create unified logger factory
cat > claude_pm/core/logging/unified_logger.py << 'EOF'
"""Unified logging factory for framework consistency."""
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

class UnifiedLogger:
    """Centralized logger factory with consistent configuration."""
    
    _loggers: Dict[str, logging.Logger] = {}
    _configured = False
    
    @classmethod
    def get_logger(cls, name: str, config: Optional[Dict[str, Any]] = None) -> logging.Logger:
        """Get configured logger by name."""
        if name not in cls._loggers:
            cls._loggers[name] = cls._create_logger(name, config)
        return cls._loggers[name]
    
    @classmethod
    def _create_logger(cls, name: str, config: Optional[Dict[str, Any]] = None) -> logging.Logger:
        """Create and configure logger."""
        logger = logging.getLogger(name)
        
        if not cls._configured:
            cls._configure_root_logger(config)
            cls._configured = True
        
        return logger
    
    @classmethod
    def _configure_root_logger(cls, config: Optional[Dict[str, Any]] = None) -> None:
        """Configure root logger settings."""
        config = config or {}
        level = config.get('level', logging.INFO)
        format_string = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        logging.basicConfig(
            level=level,
            format=format_string,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(Path.home() / '.claude-pm' / 'logs' / 'framework.log')
            ]
        )
EOF
```

#### Phase 3 Integration Testing Template

**Integration Testing Protocol**
```bash
# Create comprehensive integration test suite
cat > tests/integration/test_modular_integration.py << 'EOF'
"""Integration tests for modular architecture."""
import pytest
import asyncio
from pathlib import Path

class TestModularIntegration:
    """Test suite for validating modular component integration."""
    
    @pytest.mark.asyncio
    async def test_cli_service_coordination(self):
        """Test CLI coordinates with all services properly."""
        from claude_pm.cli.core.service_manager import CLIServiceManager
        
        manager = CLIServiceManager()
        initialized = await manager.initialize_services()
        assert initialized, "CLI service initialization failed"
        
        # Test service availability
        parent_dir_service = manager.get_service('parent_directory_manager')
        assert parent_dir_service is not None, "Parent directory manager not available"
    
    @pytest.mark.asyncio
    async def test_backup_deployment_integration(self):
        """Test backup and deployment services work together."""
        from claude_pm.services.deployment.backup_manager import BackupManager
        from claude_pm.services.deployment.framework_deployer import FrameworkDeployer
        
        backup_manager = BackupManager()
        deployer = FrameworkDeployer(backup_manager=backup_manager)
        
        # Test integration workflow
        test_path = Path('/tmp/integration_test')
        test_path.mkdir(exist_ok=True)
        
        success = await deployer.deploy_framework_template(test_path, {
            'content': 'Test template content',
            'version': '0.6.3'
        })
        
        assert success, "Integrated deployment failed"
        
        # Cleanup
        import shutil
        shutil.rmtree(test_path)
    
    def test_performance_benchmarks(self):
        """Test that performance targets are met."""
        import time
        from claude_pm.cli.main import ModularCLI
        
        # Test CLI startup time
        start_time = time.time()
        cli = ModularCLI()
        startup_time = time.time() - start_time
        
        assert startup_time < 1.0, f"CLI startup too slow: {startup_time}s"
EOF

# Run integration tests
python -m pytest tests/integration/test_modular_integration.py -v
```

## Quality Validation Commands

### Automated Quality Checks
```bash
#!/bin/bash
# Quality validation script for EP-0041

echo "🔍 Running EP-0041 Quality Validation"

# File size validation
echo "📏 Checking file size targets..."
for file in $(find claude_pm/ -name "*.py" -size +50k); do
    lines=$(wc -l "$file" | awk '{print $1}')
    echo "⚠️ Large file: $file ($lines lines)"
done

# Test coverage validation
echo "🧪 Checking test coverage..."
python -m pytest --cov=claude_pm --cov-report=term-missing --cov-fail-under=85

# Performance validation
echo "⚡ Running performance tests..."
python -m pytest tests/performance/ -v

# Code quality validation
echo "🔍 Running code quality checks..."
python -m flake8 claude_pm/ --max-line-length=100
python -m mypy claude_pm/ --ignore-missing-imports

echo "✅ Quality validation complete"
```

### Success Validation Checklist
```bash
#!/bin/bash
# EP-0041 Success validation checklist

echo "📋 EP-0041 Success Validation Checklist"

# File size targets
cli_lines=$(wc -l claude_pm/cli.py | awk '{print $1}')
if [ "$cli_lines" -lt 500 ]; then
    echo "✅ CLI module under 500 lines: $cli_lines"
else
    echo "❌ CLI module too large: $cli_lines lines"
fi

# Functionality preservation
echo "🔧 Testing functionality preservation..."
python -m claude_pm.cli --help > /dev/null && echo "✅ CLI help working" || echo "❌ CLI help broken"

# Performance targets
echo "⚡ Validating performance targets..."
# Add specific performance validation commands

echo "📊 Validation complete - check results above"
```

## Troubleshooting Guides

### Common Issues and Solutions

#### Issue: Framework Template Protection Failure
```bash
# Emergency framework template recovery
echo "🚨 Emergency Framework Template Recovery"

# Step 1: Stop all operations
echo "1. Stopping all framework operations..."

# Step 2: Restore from backup
echo "2. Restoring from latest backup..."
python -c "
import asyncio
from claude_pm.services.deployment.backup_manager import BackupManager
from pathlib import Path

async def emergency_restore():
    manager = BackupManager()
    backups = manager.list_backups()
    if backups:
        latest = backups[-1]
        success = await manager.restore_from_backup(Path('.'), latest['name'])
        print(f'Emergency restore: {success}')
    else:
        print('No backups available - manual recovery required')

asyncio.run(emergency_restore())
"

# Step 3: Validate restoration
echo "3. Validating framework integrity..."
python -c "
from pathlib import Path
claude_md = Path('CLAUDE.md')
if claude_md.exists():
    print('✅ CLAUDE.md restored')
else:
    print('❌ CLAUDE.md missing - check framework/CLAUDE.md')
"
```

#### Issue: Performance Regression
```bash
# Performance regression diagnosis
echo "📊 Performance Regression Diagnosis"

# Compare current vs baseline
echo "Comparing performance metrics..."
python scripts/performance_comparison.py baseline_metrics.json current_metrics.json

# Identify bottlenecks
echo "Identifying performance bottlenecks..."
python -m cProfile -o profile_output.prof -m claude_pm.cli --help
python -c "
import pstats
stats = pstats.Stats('profile_output.prof')
stats.sort_stats('cumulative').print_stats(10)
"
```

## Conclusion

These execution guides provide step-by-step instructions for implementing the EP-0041 Codebase Modularization Initiative. Key success factors:

1. **Follow Critical Path**: Respect dependencies, especially ISS-0114 → ISS-0115
2. **Protect Framework**: Maintain comprehensive backups and validation
3. **Validate Continuously**: Run quality checks at each milestone
4. **Monitor Performance**: Ensure no degradation throughout process

Each guide includes validation steps, troubleshooting procedures, and success criteria to ensure systematic and successful modularization.

---

**Document Authority**: Tactical Execution and Operational Guidance  
**Review Cycle**: Updated with each component completion  
**Validation**: Each step includes verification commands  
**Recovery**: Emergency procedures for critical issues