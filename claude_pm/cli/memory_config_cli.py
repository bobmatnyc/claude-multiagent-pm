#!/usr/bin/env python3
"""
Memory Configuration CLI

Command-line interface for managing memory trigger configuration and policies.
Provides tools for validation, deployment, and monitoring of memory configurations.
"""

import argparse
import os
import sys
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import subprocess

# Add the parent directory to the path so we can import from claude_pm
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude_pm.config.memory_trigger_config import (
    MemoryTriggerConfigManager,
    MemoryTriggerConfig,
    Environment,
    apply_environment_overrides
)
from claude_pm.config.policy_engine_config import (
    PolicyEngineConfig,
    PolicyEngine,
    PolicyRule,
    PolicyCondition,
    PolicyAction,
    PolicyConditionType,
    PolicyActionType,
    PolicyScope
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MemoryConfigCLI:
    """Command-line interface for memory configuration management"""
    
    def __init__(self):
        self.config_manager: Optional[MemoryTriggerConfigManager] = None
        self.policy_engine: Optional[PolicyEngine] = None
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the command-line argument parser"""
        parser = argparse.ArgumentParser(
            description='Memory Configuration Management CLI',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s validate config.yaml
  %(prog)s deploy --env production config.yaml
  %(prog)s generate --env development
  %(prog)s policy list
  %(prog)s policy add error_handler.yaml
  %(prog)s stats --config config.yaml
            """
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        
        parser.add_argument(
            '--config', '-c',
            type=str,
            help='Configuration file path'
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Validate command
        validate_parser = subparsers.add_parser('validate', help='Validate configuration file')
        validate_parser.add_argument('file', help='Configuration file to validate')
        validate_parser.add_argument('--strict', action='store_true', help='Enable strict validation')
        
        # Generate command
        generate_parser = subparsers.add_parser('generate', help='Generate configuration template')
        generate_parser.add_argument('--env', choices=['development', 'testing', 'staging', 'production'],
                                   default='development', help='Environment type')
        generate_parser.add_argument('--output', '-o', help='Output file path')
        generate_parser.add_argument('--minimal', action='store_true', help='Generate minimal configuration')
        
        # Deploy command
        deploy_parser = subparsers.add_parser('deploy', help='Deploy configuration')
        deploy_parser.add_argument('file', help='Configuration file to deploy')
        deploy_parser.add_argument('--env', choices=['development', 'testing', 'staging', 'production'],
                                 required=True, help='Target environment')
        deploy_parser.add_argument('--dry-run', action='store_true', help='Show what would be deployed')
        deploy_parser.add_argument('--backup', action='store_true', help='Create backup before deployment')
        
        # Policy commands
        policy_parser = subparsers.add_parser('policy', help='Policy management commands')
        policy_subparsers = policy_parser.add_subparsers(dest='policy_command', help='Policy operations')
        
        # Policy list
        policy_list_parser = policy_subparsers.add_parser('list', help='List policy rules')
        policy_list_parser.add_argument('--scope', choices=['global', 'agent', 'workflow', 'task', 'user', 'session'],
                                       help='Filter by scope')
        policy_list_parser.add_argument('--enabled-only', action='store_true', help='Show only enabled rules')
        
        # Policy add
        policy_add_parser = policy_subparsers.add_parser('add', help='Add policy rule')
        policy_add_parser.add_argument('file', help='Policy rule file (YAML)')
        policy_add_parser.add_argument('--validate', action='store_true', help='Validate before adding')
        
        # Policy remove
        policy_remove_parser = policy_subparsers.add_parser('remove', help='Remove policy rule')
        policy_remove_parser.add_argument('name', help='Policy rule name')
        policy_remove_parser.add_argument('--force', action='store_true', help='Force removal without confirmation')
        
        # Policy test
        policy_test_parser = policy_subparsers.add_parser('test', help='Test policy rules')
        policy_test_parser.add_argument('--context', help='Context file (JSON)')
        policy_test_parser.add_argument('--rule', help='Test specific rule')
        policy_test_parser.add_argument('--output', help='Output results to file')
        
        # Stats command
        stats_parser = subparsers.add_parser('stats', help='Show configuration statistics')
        stats_parser.add_argument('--format', choices=['text', 'json', 'yaml'], default='text',
                                help='Output format')
        
        # Monitor command
        monitor_parser = subparsers.add_parser('monitor', help='Monitor configuration health')
        monitor_parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
        monitor_parser.add_argument('--alerts', action='store_true', help='Enable alert notifications')
        
        # Backup/Restore commands
        backup_parser = subparsers.add_parser('backup', help='Backup configuration')
        backup_parser.add_argument('--output', '-o', help='Backup file path')
        backup_parser.add_argument('--include-policies', action='store_true', help='Include policy rules')
        
        restore_parser = subparsers.add_parser('restore', help='Restore configuration')
        restore_parser.add_argument('file', help='Backup file to restore')
        restore_parser.add_argument('--dry-run', action='store_true', help='Show what would be restored')
        
        return parser
    
    def run(self, args: List[str] = None) -> int:
        """Run the CLI with the given arguments"""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        if parsed_args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        try:
            # Load configuration if specified
            if parsed_args.config:
                self.config_manager = MemoryTriggerConfigManager(parsed_args.config)
            
            # Route to appropriate command handler
            if parsed_args.command == 'validate':
                return self.cmd_validate(parsed_args)
            elif parsed_args.command == 'generate':
                return self.cmd_generate(parsed_args)
            elif parsed_args.command == 'deploy':
                return self.cmd_deploy(parsed_args)
            elif parsed_args.command == 'policy':
                return self.cmd_policy(parsed_args)
            elif parsed_args.command == 'stats':
                return self.cmd_stats(parsed_args)
            elif parsed_args.command == 'monitor':
                return self.cmd_monitor(parsed_args)
            elif parsed_args.command == 'backup':
                return self.cmd_backup(parsed_args)
            elif parsed_args.command == 'restore':
                return self.cmd_restore(parsed_args)
            else:
                parser.print_help()
                return 1
                
        except Exception as e:
            logger.error(f"Command failed: {e}")
            if parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def cmd_validate(self, args) -> int:
        """Validate configuration file"""
        config_file = Path(args.file)
        
        if not config_file.exists():
            logger.error(f"Configuration file not found: {config_file}")
            return 1
        
        try:
            # Load and validate configuration
            manager = MemoryTriggerConfigManager()
            manager.load_config_from_file(str(config_file))
            
            config = manager.get_config()
            
            # Set validation strictness
            if args.strict:
                config.validation_strict = True
            
            # Validate configuration
            errors = config.validate()
            
            if errors:
                print(f"❌ Configuration validation failed:")
                for error in errors:
                    print(f"  • {error}")
                return 1
            else:
                print(f"✅ Configuration is valid")
                
                # Show configuration summary
                print(f"\nConfiguration Summary:")
                print(f"  Environment: {config.environment.value}")
                print(f"  Version: {config.config_version}")
                print(f"  Global enabled: {config.global_enabled}")
                print(f"  Backend: {config.backend.backend_type.value}")
                print(f"  Trigger policies: {len(config.trigger_policies)}")
                
                return 0
                
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return 1
    
    def cmd_generate(self, args) -> int:
        """Generate configuration template"""
        try:
            env = Environment(args.env)
            
            if args.minimal:
                # Generate minimal configuration
                config = MemoryTriggerConfig(environment=env)
            else:
                # Load environment-specific template
                template_path = Path(__file__).parent.parent / "config" / "environments" / f"{args.env}.yaml"
                
                if template_path.exists():
                    with open(template_path, 'r') as f:
                        template_data = yaml.safe_load(f)
                    config = MemoryTriggerConfig.from_dict(template_data)
                else:
                    # Use default configuration
                    config = MemoryTriggerConfig(environment=env)
            
            # Convert to dictionary and YAML
            config_dict = config.to_dict()
            self._convert_enums_to_strings(config_dict)
            
            yaml_content = yaml.dump(config_dict, default_flow_style=False, indent=2)
            
            if args.output:
                output_path = Path(args.output)
                with open(output_path, 'w') as f:
                    f.write(yaml_content)
                print(f"✅ Configuration template generated: {output_path}")
            else:
                print(yaml_content)
            
            return 0
            
        except Exception as e:
            logger.error(f"Template generation failed: {e}")
            return 1
    
    def cmd_deploy(self, args) -> int:
        """Deploy configuration"""
        config_file = Path(args.file)
        
        if not config_file.exists():
            logger.error(f"Configuration file not found: {config_file}")
            return 1
        
        try:
            # Create backup if requested
            if args.backup:
                backup_path = config_file.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml')
                if config_file.exists():
                    import shutil
                    shutil.copy2(config_file, backup_path)
                    print(f"📁 Backup created: {backup_path}")
            
            # Load and validate configuration
            manager = MemoryTriggerConfigManager()
            manager.load_config_from_file(str(config_file))
            
            config = manager.get_config()
            
            # Verify environment matches
            target_env = Environment(args.env)
            if config.environment != target_env:
                if not args.dry_run:
                    logger.warning(f"Configuration environment ({config.environment.value}) " +
                                 f"doesn't match target environment ({target_env.value})")
                    config.environment = target_env
            
            # Apply environment variable overrides
            apply_environment_overrides(config)
            
            # Validate configuration
            errors = config.validate()
            if errors:
                logger.error(f"Configuration validation failed:")
                for error in errors:
                    logger.error(f"  • {error}")
                return 1
            
            if args.dry_run:
                print(f"🔍 Dry run - Configuration would be deployed:")
                print(f"  Environment: {config.environment.value}")
                print(f"  Backend: {config.backend.backend_type.value}")
                print(f"  Trigger policies: {len(config.trigger_policies)}")
                print(f"  Global enabled: {config.global_enabled}")
                return 0
            
            # Deploy configuration
            # In a real implementation, this would deploy to the target environment
            print(f"🚀 Deploying configuration to {target_env.value} environment...")
            
            # Save configuration with environment-specific settings
            env_config_path = config_file.parent / f"config.{target_env.value}.yaml"
            manager.save_config_to_file(str(env_config_path))
            
            print(f"✅ Configuration deployed successfully")
            print(f"   Config file: {env_config_path}")
            print(f"   Environment: {config.environment.value}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return 1
    
    def cmd_policy(self, args) -> int:
        """Handle policy management commands"""
        if not self.config_manager:
            # Try to load default configuration
            if args.config:
                self.config_manager = MemoryTriggerConfigManager(args.config)
            else:
                self.config_manager = MemoryTriggerConfigManager()
        
        if args.policy_command == 'list':
            return self.cmd_policy_list(args)
        elif args.policy_command == 'add':
            return self.cmd_policy_add(args)
        elif args.policy_command == 'remove':
            return self.cmd_policy_remove(args)
        elif args.policy_command == 'test':
            return self.cmd_policy_test(args)
        else:
            print("Available policy commands: list, add, remove, test")
            return 1
    
    def cmd_policy_list(self, args) -> int:
        """List policy rules"""
        try:
            if not self.policy_engine:
                self.policy_engine = PolicyEngine()
            
            scope = PolicyScope(args.scope) if args.scope else None
            rules = self.policy_engine.list_rules(scope=scope, enabled_only=args.enabled_only)
            
            if not rules:
                print("No policy rules found")
                return 0
            
            print(f"Policy Rules ({len(rules)}):")
            print("-" * 60)
            
            for rule in rules:
                status = "✅" if rule.enabled else "❌"
                print(f"{status} {rule.name} (priority: {rule.priority}, scope: {rule.scope.value})")
                if rule.description:
                    print(f"   {rule.description}")
                print(f"   Conditions: {len(rule.conditions)}, Actions: {len(rule.actions)}")
                if rule.max_executions:
                    print(f"   Executions: {rule.execution_count}/{rule.max_executions}")
                print()
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to list policy rules: {e}")
            return 1
    
    def cmd_policy_add(self, args) -> int:
        """Add policy rule"""
        policy_file = Path(args.file)
        
        if not policy_file.exists():
            logger.error(f"Policy file not found: {policy_file}")
            return 1
        
        try:
            # Load policy configuration
            with open(policy_file, 'r') as f:
                policy_data = yaml.safe_load(f)
            
            if not self.policy_engine:
                self.policy_engine = PolicyEngine()
            
            # Import policy rules
            errors = self.policy_engine.import_rules(policy_data.get('rules', {}))
            
            if errors:
                logger.error("Failed to import policy rules:")
                for error in errors:
                    logger.error(f"  • {error}")
                return 1
            
            print(f"✅ Policy rules imported successfully from {policy_file}")
            
            # Show imported rules
            imported_count = len(policy_data.get('rules', {}))
            print(f"   Imported {imported_count} rule(s)")
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to add policy rule: {e}")
            return 1
    
    def cmd_policy_remove(self, args) -> int:
        """Remove policy rule"""
        try:
            if not self.policy_engine:
                self.policy_engine = PolicyEngine()
            
            if not args.force:
                response = input(f"Are you sure you want to remove policy rule '{args.name}'? [y/N]: ")
                if response.lower() != 'y':
                    print("Cancelled")
                    return 0
            
            success = self.policy_engine.remove_rule(args.name)
            
            if success:
                print(f"✅ Policy rule '{args.name}' removed successfully")
                return 0
            else:
                logger.error(f"Policy rule '{args.name}' not found")
                return 1
                
        except Exception as e:
            logger.error(f"Failed to remove policy rule: {e}")
            return 1
    
    def cmd_policy_test(self, args) -> int:
        """Test policy rules"""
        try:
            # Load test context
            if args.context:
                context_file = Path(args.context)
                if not context_file.exists():
                    logger.error(f"Context file not found: {context_file}")
                    return 1
                
                with open(context_file, 'r') as f:
                    context = json.load(f)
            else:
                # Use default test context
                context = {
                    "agent_name": "test_agent",
                    "operation": "test_operation",
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "environment": "testing"
                }
            
            if not self.policy_engine:
                self.policy_engine = PolicyEngine()
            
            # Execute policy rules
            if args.rule:
                # Test specific rule
                rule = self.policy_engine.get_rule(args.rule)
                if not rule:
                    logger.error(f"Policy rule '{args.rule}' not found")
                    return 1
                
                results = [self.policy_engine._execute_rule(rule, context)]
            else:
                # Test all applicable rules
                results = self.policy_engine.execute_rules(context)
            
            # Format results
            test_results = {
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "results": results,
                "summary": {
                    "total_rules": len(results),
                    "successful": len([r for r in results if r['success']]),
                    "failed": len([r for r in results if not r['success']])
                }
            }
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(test_results, f, indent=2)
                print(f"✅ Test results saved to {args.output}")
            else:
                print(json.dumps(test_results, indent=2))
            
            return 0
            
        except Exception as e:
            logger.error(f"Policy test failed: {e}")
            return 1
    
    def cmd_stats(self, args) -> int:
        """Show configuration statistics"""
        try:
            if not self.config_manager:
                logger.error("No configuration loaded")
                return 1
            
            config = self.config_manager.get_config()
            
            # Gather statistics
            stats = {
                "configuration": {
                    "environment": config.environment.value,
                    "version": config.config_version,
                    "global_enabled": config.global_enabled,
                    "validation_strict": config.validation_strict
                },
                "performance": {
                    "max_operations_per_second": config.max_memory_operations_per_second,
                    "batch_size": config.performance.batch_size,
                    "max_concurrent": config.performance.max_concurrent_operations,
                    "cache_enabled": config.performance.cache_enabled,
                    "background_processing": config.performance.background_processing_enabled
                },
                "backend": {
                    "type": config.backend.backend_type.value,
                    "pool_enabled": config.backend.pool_enabled,
                    "pool_size": config.backend.pool_size,
                    "encryption_enabled": config.backend.encryption_enabled,
                    "failover_enabled": config.backend.failover_enabled
                },
                "policies": {
                    "count": len(config.trigger_policies),
                    "enabled": len([p for p in config.trigger_policies.values() if p.enabled]),
                    "types": list(set(p.trigger_type.value for p in config.trigger_policies.values()))
                },
                "features": {
                    "enabled_features": [k for k, v in config.features.items() if v],
                    "disabled_features": [k for k, v in config.features.items() if not v]
                }
            }
            
            # Format output
            if args.format == 'json':
                print(json.dumps(stats, indent=2))
            elif args.format == 'yaml':
                print(yaml.dump(stats, default_flow_style=False, indent=2))
            else:
                # Text format
                print("Configuration Statistics")
                print("=" * 50)
                print(f"Environment: {stats['configuration']['environment']}")
                print(f"Version: {stats['configuration']['version']}")
                print(f"Global Enabled: {stats['configuration']['global_enabled']}")
                print()
                print(f"Performance:")
                print(f"  Max Ops/sec: {stats['performance']['max_operations_per_second']}")
                print(f"  Batch Size: {stats['performance']['batch_size']}")
                print(f"  Max Concurrent: {stats['performance']['max_concurrent']}")
                print(f"  Cache: {stats['performance']['cache_enabled']}")
                print()
                print(f"Backend:")
                print(f"  Type: {stats['backend']['type']}")
                print(f"  Pool: {stats['backend']['pool_enabled']} (size: {stats['backend']['pool_size']})")
                print(f"  Encryption: {stats['backend']['encryption_enabled']}")
                print()
                print(f"Policies:")
                print(f"  Total: {stats['policies']['count']}")
                print(f"  Enabled: {stats['policies']['enabled']}")
                print(f"  Types: {', '.join(stats['policies']['types'])}")
                print()
                print(f"Features:")
                print(f"  Enabled: {', '.join(stats['features']['enabled_features'])}")
                if stats['features']['disabled_features']:
                    print(f"  Disabled: {', '.join(stats['features']['disabled_features'])}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to generate statistics: {e}")
            return 1
    
    def cmd_monitor(self, args) -> int:
        """Monitor configuration health"""
        try:
            if not self.config_manager:
                logger.error("No configuration loaded")
                return 1
            
            print(f"🔍 Monitoring configuration health (interval: {args.interval}s)")
            print("Press Ctrl+C to stop")
            
            import time
            
            while True:
                try:
                    # Check configuration health
                    config = self.config_manager.get_config()
                    errors = config.validate()
                    
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    if errors:
                        status = "❌ UNHEALTHY"
                        print(f"[{timestamp}] {status} - {len(errors)} errors")
                        for error in errors[:3]:  # Show first 3 errors
                            print(f"  • {error}")
                        if len(errors) > 3:
                            print(f"  ... and {len(errors) - 3} more errors")
                        
                        if args.alerts:
                            # In a real implementation, this would send alerts
                            logger.warning(f"Configuration health alert: {len(errors)} errors detected")
                    else:
                        status = "✅ HEALTHY"
                        print(f"[{timestamp}] {status}")
                    
                    time.sleep(args.interval)
                    
                except KeyboardInterrupt:
                    print("\n👋 Monitoring stopped")
                    break
            
            return 0
            
        except Exception as e:
            logger.error(f"Monitoring failed: {e}")
            return 1
    
    def cmd_backup(self, args) -> int:
        """Backup configuration"""
        try:
            if not self.config_manager:
                logger.error("No configuration loaded")
                return 1
            
            # Create backup data
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "configuration": self.config_manager.get_config().to_dict()
            }
            
            # Include policies if requested
            if args.include_policies and self.policy_engine:
                backup_data["policies"] = self.policy_engine.export_rules()
            
            # Convert enums to strings
            self._convert_enums_to_strings(backup_data)
            
            # Determine output file
            if args.output:
                backup_file = Path(args.output)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = Path(f"memory_config_backup_{timestamp}.yaml")
            
            # Save backup
            with open(backup_file, 'w') as f:
                yaml.dump(backup_data, f, default_flow_style=False, indent=2)
            
            print(f"✅ Configuration backup created: {backup_file}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return 1
    
    def cmd_restore(self, args) -> int:
        """Restore configuration"""
        backup_file = Path(args.file)
        
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return 1
        
        try:
            # Load backup data
            with open(backup_file, 'r') as f:
                backup_data = yaml.safe_load(f)
            
            if args.dry_run:
                print(f"🔍 Dry run - Configuration would be restored from:")
                print(f"  Backup file: {backup_file}")
                print(f"  Backup timestamp: {backup_data.get('timestamp', 'Unknown')}")
                
                if 'configuration' in backup_data:
                    config_data = backup_data['configuration']
                    print(f"  Environment: {config_data.get('environment', 'Unknown')}")
                    print(f"  Version: {config_data.get('config_version', 'Unknown')}")
                
                if 'policies' in backup_data:
                    policies = backup_data['policies']
                    print(f"  Policies: {len(policies)} rules")
                
                return 0
            
            # Restore configuration
            if 'configuration' in backup_data:
                config = MemoryTriggerConfig.from_dict(backup_data['configuration'])
                
                # Validate restored configuration
                errors = config.validate()
                if errors:
                    logger.error("Restored configuration is invalid:")
                    for error in errors:
                        logger.error(f"  • {error}")
                    return 1
                
                # Update config manager
                self.config_manager = MemoryTriggerConfigManager()
                self.config_manager.config = config
                
                print(f"✅ Configuration restored from {backup_file}")
            
            # Restore policies if present
            if 'policies' in backup_data:
                if not self.policy_engine:
                    self.policy_engine = PolicyEngine()
                
                errors = self.policy_engine.import_rules(backup_data['policies'])
                if errors:
                    logger.warning("Some policy rules failed to restore:")
                    for error in errors:
                        logger.warning(f"  • {error}")
                else:
                    print(f"✅ Policy rules restored")
            
            return 0
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return 1
    
    def _convert_enums_to_strings(self, data: Any) -> None:
        """Convert enum values to strings for YAML serialization"""
        if isinstance(data, dict):
            for key, value in data.items():
                if hasattr(value, 'value'):  # Enum
                    data[key] = value.value
                else:
                    self._convert_enums_to_strings(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if hasattr(item, 'value'):  # Enum
                    data[i] = item.value
                else:
                    self._convert_enums_to_strings(item)


def main():
    """Main entry point for the CLI"""
    cli = MemoryConfigCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())