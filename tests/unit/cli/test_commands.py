#!/usr/bin/env python3
"""Tests for CLI command modules and registration."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from click.testing import CliRunner
import click

from claude_pm.cli import (
    ModularCLI, 
    get_cli, 
    create_modular_cli,
    register_external_commands,
    get_available_models,
    format_model_help,
    _resolve_model_selection
)


class TestModularCLI:
    """Test suite for ModularCLI class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.cli = ModularCLI()
        self.runner = CliRunner()
    
    def test_create_cli_group(self):
        """Test CLI group creation."""
        cli_group = self.cli.create_cli_group()
        
        assert cli_group is not None
        assert self.cli.cli_group is not None
        assert hasattr(cli_group, 'command')
        assert hasattr(cli_group, 'group')
    
    def test_cli_group_attributes(self):
        """Test CLI group has expected attributes."""
        cli_group = self.cli.create_cli_group()
        
        # Test the group has the expected options
        assert any(opt.name == 'verbose' for opt in cli_group.params)
        assert any(opt.name == 'config' for opt in cli_group.params)
        assert any(opt.name == 'model' for opt in cli_group.params)
    
    def test_load_command_modules(self):
        """Test command module loading."""
        self.cli.create_cli_group()
        
        with patch('claude_pm.cli.setup_commands.register_setup_commands') as mock_setup:
            with patch('claude_pm.cli.test_commands.register_test_commands') as mock_test:
                with patch('claude_pm.cli.productivity_commands.register_productivity_commands') as mock_prod:
                    with patch('claude_pm.cli.deployment_commands.register_deployment_commands') as mock_deploy:
                        with patch('claude_pm.cli.system_commands.register_system_commands') as mock_system:
                            self.cli.load_command_modules()
                            
                            # Verify all modules were loaded
                            mock_setup.assert_called_once_with(self.cli.cli_group)
                            mock_test.assert_called_once_with(self.cli.cli_group)
                            mock_prod.assert_called_once_with(self.cli.cli_group)
                            mock_deploy.assert_called_once_with(self.cli.cli_group)
                            mock_system.assert_called_once_with(self.cli.cli_group)
                            
                            assert self.cli.modules_loaded is True
    
    def test_load_command_modules_error(self):
        """Test command module loading error handling."""
        self.cli.create_cli_group()
        
        with patch('claude_pm.cli.setup_commands.register_setup_commands') as mock_setup:
            mock_setup.side_effect = Exception("Test error")
            
            with pytest.raises(Exception):
                self.cli.load_command_modules()
    
    def test_load_command_modules_idempotent(self):
        """Test command modules are only loaded once."""
        self.cli.create_cli_group()
        
        with patch('claude_pm.cli.setup_commands.register_setup_commands') as mock_setup:
            # First load
            self.cli.load_command_modules()
            assert mock_setup.call_count == 1
            
            # Second load should not call again
            self.cli.load_command_modules()
            assert mock_setup.call_count == 1
    
    def test_get_cli(self):
        """Test get_cli creates and loads everything."""
        with patch.object(self.cli, 'create_cli_group') as mock_create:
            with patch.object(self.cli, 'load_command_modules') as mock_load:
                mock_create.return_value = Mock()
                
                cli = self.cli.get_cli()
                
                mock_create.assert_called_once()
                mock_load.assert_called_once()
                assert cli is not None
    
    def test_get_cli_reuses_instance(self):
        """Test get_cli reuses existing instance."""
        with patch.object(self.cli, 'load_command_modules'):
            cli1 = self.cli.get_cli()
            cli2 = self.cli.get_cli()
            
            assert cli1 is cli2


class TestModelResolution:
    """Test suite for model resolution functionality."""
    
    def test_resolve_model_selection_aliases(self):
        """Test model selection with aliases."""
        assert _resolve_model_selection('sonnet') == 'claude-sonnet-4-20250514'
        assert _resolve_model_selection('opus') == 'claude-4-opus'
        assert _resolve_model_selection('haiku') == 'claude-3-haiku-20240307'
        assert _resolve_model_selection('sonnet4') == 'claude-sonnet-4-20250514'
        assert _resolve_model_selection('opus4') == 'claude-4-opus'
        assert _resolve_model_selection('sonnet3') == 'claude-3-5-sonnet-20241022'
        assert _resolve_model_selection('opus3') == 'claude-3-opus-20240229'
    
    def test_resolve_model_selection_case_insensitive(self):
        """Test model selection is case insensitive."""
        assert _resolve_model_selection('SONNET') == 'claude-sonnet-4-20250514'
        assert _resolve_model_selection('Opus') == 'claude-4-opus'
        assert _resolve_model_selection('HaiKu') == 'claude-3-haiku-20240307'
    
    def test_resolve_model_selection_direct_id(self):
        """Test model selection with direct model IDs."""
        # Mock ModelType enum for testing
        with patch('claude_pm.cli.ModelType') as mock_model_type:
            mock_model_type.__iter__.return_value = [
                Mock(value='claude-3-haiku-20240307'),
                Mock(value='claude-sonnet-4-20250514')
            ]
            
            assert _resolve_model_selection('claude-3-haiku-20240307') == 'claude-3-haiku-20240307'
    
    def test_resolve_model_selection_partial_match(self):
        """Test model selection with partial matches."""
        with patch('claude_pm.cli.ModelType') as mock_model_type:
            mock_model_type.__iter__.return_value = [
                Mock(value='claude-3-haiku-20240307'),
                Mock(value='claude-sonnet-4-20250514')
            ]
            
            # Partial match should work
            assert _resolve_model_selection('haiku-20240307') == 'claude-3-haiku-20240307'
    
    def test_resolve_model_selection_invalid(self):
        """Test model selection with invalid input."""
        assert _resolve_model_selection('invalid_model') is None
        assert _resolve_model_selection('') is None
        assert _resolve_model_selection(None) is None
        assert _resolve_model_selection('   ') is None  # Whitespace only
        assert _resolve_model_selection('\t\n') is None  # Other whitespace
    
    def test_get_available_models(self):
        """Test get_available_models returns expected aliases."""
        models = get_available_models()
        
        assert isinstance(models, dict)
        assert 'sonnet' in models
        assert 'opus' in models
        assert 'haiku' in models
        assert models['sonnet'] == 'claude-sonnet-4-20250514'
        assert models['opus'] == 'claude-4-opus'
    
    def test_format_model_help(self):
        """Test format_model_help output."""
        help_text = format_model_help()
        
        assert 'Available models and aliases:' in help_text
        assert 'Claude 4 models' in help_text
        assert 'Claude 3 models' in help_text
        assert 'sonnet ->' in help_text
        assert 'opus ->' in help_text
        assert 'Examples:' in help_text
        assert '--model sonnet' in help_text


class TestExternalCommands:
    """Test suite for external command registration."""
    
    def test_register_external_commands(self):
        """Test external commands are registered."""
        mock_cli_group = Mock()
        
        with patch('claude_pm.cli_flags.cli_flags') as mock_flags:
            with patch('claude_pm.cli_enforcement.enforcement_cli') as mock_enforcement:
                with patch('claude_pm.cmpm_commands.register_cmpm_commands') as mock_cmpm:
                    with patch('claude_pm.cli_deployment_integration.integrate_deployment_system') as mock_deploy:
                        register_external_commands(mock_cli_group)
                        
                        # Verify commands were added
                        mock_cli_group.add_command.assert_any_call(mock_flags, name="flags")
                        mock_cli_group.add_command.assert_any_call(mock_enforcement)
                        mock_cmpm.assert_called_once_with(mock_cli_group)
                        mock_deploy.assert_called_once_with(mock_cli_group)
    
    def test_register_external_commands_handles_errors(self):
        """Test external command registration handles import errors."""
        mock_cli_group = Mock()
        
        # All imports fail
        with patch('claude_pm.cli_flags.cli_flags', side_effect=ImportError):
            with patch('claude_pm.cli_enforcement.enforcement_cli', side_effect=ImportError):
                with patch('claude_pm.cmpm_commands.register_cmpm_commands', side_effect=ImportError):
                    with patch('claude_pm.cli_deployment_integration.integrate_deployment_system', side_effect=ImportError):
                        # Should not raise, just log warnings
                        register_external_commands(mock_cli_group)


class TestCLIIntegration:
    """Test suite for full CLI integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
    
    def test_create_modular_cli_full(self):
        """Test create_modular_cli creates complete CLI."""
        with patch('claude_pm.cli.__init__._display_directory_context'):
            with patch('claude_pm.cli.__init__.register_external_commands') as mock_register:
                cli = create_modular_cli()
                
                assert cli is not None
                mock_register.assert_called_once()
    
    def test_cli_model_override_in_context(self):
        """Test model override is stored in context."""
        with patch('claude_pm.cli.__init__._display_directory_context'):
            cli = create_modular_cli()
            
            @cli.command()
            @click.pass_context
            def test_model(ctx):
                model = ctx.obj.get('model')
                click.echo(f'Model: {model}')
            
            result = self.runner.invoke(cli, ['--model', 'opus', 'test_model'])
            
            assert result.exit_code == 0
            assert 'Model: claude-4-opus' in result.output
    
    def test_cli_verbose_output(self):
        """Test verbose flag produces extra output."""
        with patch('claude_pm.cli.__init__._display_directory_context'):
            cli = create_modular_cli()
            
            result = self.runner.invoke(cli, ['--verbose', '--model', 'sonnet', '--help'])
            
            assert result.exit_code == 0
            # In verbose mode, should show framework version
            # Check for verbose output indicators
    
    def test_get_cli_singleton(self):
        """Test get_cli returns singleton instance."""
        with patch('claude_pm.cli.__init__.register_external_commands'):
            cli1 = get_cli()
            cli2 = get_cli()
            
            assert cli1 is cli2