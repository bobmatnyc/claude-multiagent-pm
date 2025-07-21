#!/usr/bin/env python3
"""Tests for CLI utility functions."""

import pytest
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
import json
import time

import click
from click.testing import CliRunner

from claude_pm.cli.cli_utils import (
    get_framework_config,
    get_claude_pm_path,
    get_managed_path,
    get_model_override,
    create_model_selector_with_override,
    create_pm_orchestrator_with_cli_context,
    create_task_tool_helper_with_cli_context,
    _get_framework_version,
    _display_directory_context,
    _display_directory_context_streaming,
    async_command,
    timed_operation,
    confirm_action,
    format_table_data,
    format_status_panel,
    handle_service_errors,
    validate_project_name,
    format_duration,
    safe_json_loads,
    truncate_string,
    format_file_size,
    CLIContext,
    load_config_file,
    save_config_file,
    check_dependency,
    get_system_info,
    common_options,
    common_options_with_model
)


class TestConfigUtilities:
    """Test suite for configuration utility functions."""
    
    def test_get_framework_config(self):
        """Test getting framework configuration."""
        with patch('claude_pm.cli.cli_utils.Config') as mock_config:
            mock_instance = Mock()
            mock_config.return_value = mock_instance
            
            config = get_framework_config()
            
            assert config == mock_instance
            mock_config.assert_called_once()
    
    def test_get_claude_pm_path(self):
        """Test getting Claude PM path."""
        with patch('claude_pm.cli.cli_utils.get_framework_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get.return_value = '/test/path'
            mock_get_config.return_value = mock_config
            
            path = get_claude_pm_path()
            
            assert isinstance(path, Path)
            assert str(path) == '/test/path'
            mock_config.get.assert_called_once_with('claude_pm_path')
    
    def test_get_managed_path(self):
        """Test getting managed projects path."""
        with patch('claude_pm.cli.cli_utils.get_framework_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get.return_value = '/test/managed'
            mock_get_config.return_value = mock_config
            
            path = get_managed_path()
            
            assert isinstance(path, Path)
            assert str(path) == '/test/managed'
            mock_config.get.assert_called_once_with('managed_projects_path')


class TestModelOverride:
    """Test suite for model override functionality."""
    
    def test_get_model_override_present(self):
        """Test getting model override when present."""
        ctx = Mock()
        ctx.obj = {'model': 'claude-4-opus'}
        
        result = get_model_override(ctx)
        
        assert result == 'claude-4-opus'
    
    def test_get_model_override_absent(self):
        """Test getting model override when not present."""
        ctx = Mock()
        ctx.obj = {'other': 'value'}
        
        result = get_model_override(ctx)
        
        assert result is None
    
    def test_get_model_override_no_obj(self):
        """Test getting model override with no obj."""
        ctx = Mock()
        ctx.obj = None
        
        result = get_model_override(ctx)
        
        assert result is None
    
    def test_get_model_override_no_ctx(self):
        """Test getting model override with no context."""
        result = get_model_override(None)
        
        assert result is None
    
    def test_create_model_selector_with_override(self):
        """Test creating model selector with override."""
        ctx = Mock()
        ctx.obj = {'model': 'test-model'}
        
        with patch('claude_pm.cli.cli_utils.ModelSelector') as mock_selector:
            with patch.dict(os.environ, {}, clear=True):
                selector = create_model_selector_with_override(ctx)
                
                # Check environment was set temporarily
                assert 'CLAUDE_PM_MODEL_OVERRIDE' not in os.environ
                mock_selector.assert_called_once()
    
    def test_create_model_selector_no_override(self):
        """Test creating model selector without override."""
        ctx = Mock()
        ctx.obj = {}
        
        with patch('claude_pm.cli.cli_utils.ModelSelector') as mock_selector:
            selector = create_model_selector_with_override(ctx)
            
            mock_selector.assert_called_once()
    
    def test_create_model_selector_preserves_env(self):
        """Test model selector preserves existing environment."""
        ctx = Mock()
        ctx.obj = {'model': 'new-model'}
        
        with patch('claude_pm.cli.cli_utils.ModelSelector') as mock_selector:
            # Set existing environment variable
            os.environ['CLAUDE_PM_MODEL_OVERRIDE'] = 'old-model'
            
            try:
                selector = create_model_selector_with_override(ctx)
                
                # Should restore original value
                assert os.environ['CLAUDE_PM_MODEL_OVERRIDE'] == 'old-model'
            finally:
                del os.environ['CLAUDE_PM_MODEL_OVERRIDE']


class TestPMOrchestratorCreation:
    """Test suite for PM Orchestrator creation."""
    
    def test_create_pm_orchestrator_with_context(self):
        """Test creating PM orchestrator with CLI context."""
        ctx = Mock()
        ctx.obj = {'model': 'test-model'}
        
        with patch('claude_pm.cli.cli_utils.PMOrchestrator') as mock_orchestrator:
            result = create_pm_orchestrator_with_cli_context(ctx)
            
            mock_orchestrator.assert_called_once()
            
            # Check model override was passed
            call_kwargs = mock_orchestrator.call_args.kwargs
            assert call_kwargs.get('model_override') == 'test-model'
            assert call_kwargs.get('model_config')['source'] == 'cli_override'
    
    def test_create_pm_orchestrator_with_working_dir(self):
        """Test creating PM orchestrator with working directory."""
        ctx = Mock()
        ctx.obj = {}
        working_dir = Path('/test/dir')
        
        with patch('claude_pm.cli.cli_utils.PMOrchestrator') as mock_orchestrator:
            result = create_pm_orchestrator_with_cli_context(ctx, working_dir)
            
            call_kwargs = mock_orchestrator.call_args.kwargs
            assert call_kwargs.get('working_directory') == working_dir
    
    def test_create_task_tool_helper_with_context(self):
        """Test creating task tool helper with CLI context."""
        ctx = Mock()
        ctx.obj = {'model': 'test-model'}
        
        with patch('claude_pm.cli.cli_utils.TaskToolHelper') as mock_helper:
            result = create_task_tool_helper_with_cli_context(ctx)
            
            mock_helper.assert_called_once()
            
            # Check model override was passed
            call_kwargs = mock_helper.call_args.kwargs
            assert call_kwargs.get('model_override') == 'test-model'
            assert call_kwargs.get('model_config')['source'] == 'cli_override'


class TestAsyncCommandExecution:
    """Test suite for async command execution."""
    
    @pytest.mark.asyncio
    async def test_async_command_decorator(self):
        """Test async command decorator."""
        @async_command
        async def test_func(value):
            return f"result: {value}"
        
        # Test successful execution
        with patch('asyncio.run') as mock_run:
            mock_run.return_value = "result: test"
            result = test_func("test")
            assert result == "result: test"
    
    def test_async_command_keyboard_interrupt(self):
        """Test async command handles keyboard interrupt."""
        @async_command
        async def test_func():
            return "result"
        
        with patch('asyncio.run', side_effect=KeyboardInterrupt):
            with patch('claude_pm.cli.cli_utils.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    test_func()
                assert exc_info.value.code == 130
                mock_console.print.assert_called()
    
    def test_async_command_exception(self):
        """Test async command handles exceptions."""
        @async_command
        async def test_func():
            raise ValueError("Test error")
        
        with patch('asyncio.run', side_effect=ValueError("Test error")):
            with patch('claude_pm.cli.cli_utils.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    test_func()
                assert exc_info.value.code == 1
                mock_console.print.assert_called()


class TestTimedOperation:
    """Test suite for timed operation decorator."""
    
    def test_timed_operation_success(self):
        """Test timed operation with successful execution."""
        @timed_operation("Test operation")
        def test_func():
            time.sleep(0.01)
            return "result"
        
        with patch('claude_pm.cli.cli_utils.console') as mock_console:
            result = test_func()
            
            assert result == "result"
            mock_console.print.assert_called()
            # Check that timing info was printed
            call_args = str(mock_console.print.call_args)
            assert "Test operation completed" in call_args
            assert "ms" in call_args
    
    def test_timed_operation_failure(self):
        """Test timed operation with exception."""
        @timed_operation("Failed operation")
        def test_func():
            time.sleep(0.01)
            raise ValueError("Test error")
        
        with patch('claude_pm.cli.cli_utils.console') as mock_console:
            with pytest.raises(ValueError):
                test_func()
            
            # Should still print timing info
            mock_console.print.assert_called()
            call_args = str(mock_console.print.call_args)
            assert "Failed operation failed" in call_args


class TestUtilityFunctions:
    """Test suite for utility functions."""
    
    def test_confirm_action(self):
        """Test confirming action."""
        with patch('claude_pm.cli.cli_utils.Confirm.ask') as mock_confirm:
            mock_confirm.return_value = True
            
            result = confirm_action("Delete everything?")
            
            assert result is True
            mock_confirm.assert_called_once_with("Delete everything?", default=False)
    
    def test_format_table_data(self):
        """Test formatting table data."""
        data = [
            {'name': 'Test1', 'status': 'active'},
            {'name': 'Test2', 'status': 'inactive'}
        ]
        columns = {'name': 'cyan', 'status': 'green'}
        
        table = format_table_data(data, "Test Table", columns)
        
        assert table.title == "Test Table"
        assert len(table.columns) == 2
    
    def test_format_status_panel(self):
        """Test formatting status panel."""
        data = {
            'current_status': 'running',
            'last_update': '2023-12-25'
        }
        
        panel = format_status_panel(data, "System Status")
        
        assert panel.title == "System Status"
        assert "Current Status" in panel.renderable
        assert "Last Update" in panel.renderable


class TestDirectoryContext:
    """Test suite for directory context display."""
    
    def test_display_directory_context(self):
        """Test displaying directory context."""
        with patch('claude_pm.cli.cli_utils.get_claude_pm_path') as mock_claude_path:
            with patch('claude_pm.cli.cli_utils.console') as mock_console:
                with patch('claude_pm.cli.cli_utils.Path') as mock_path:
                    mock_claude_path.return_value = Path('/framework/path')
                    mock_path.cwd.return_value = Path('/current/dir')
                    
                    _display_directory_context()
                    
                    # Should print deployment and working directories
                    assert mock_console.print.called
                    assert mock_console.print.call_count >= 2
    
    def test_display_directory_context_streaming(self):
        """Test displaying directory context with streaming."""
        with patch('claude_pm.cli.cli_utils.setup_streaming_logger') as mock_setup:
            with patch('claude_pm.cli.cli_utils.finalize_streaming_logs') as mock_finalize:
                mock_logger = Mock()
                mock_setup.return_value = mock_logger
                
                _display_directory_context_streaming()
                
                mock_setup.assert_called_once_with("directory_context")
                mock_logger.info.assert_called()
                mock_finalize.assert_called_once_with(mock_logger)
    
    def test_get_framework_version(self):
        """Test getting framework version."""
        with patch('claude_pm.cli.cli_utils.Path') as mock_path:
            mock_version_file = Mock()
            mock_version_file.exists.return_value = True
            mock_version_file.read_text.return_value = "1.0.0\n"
            mock_path.return_value.parent.parent.parent.__truediv__.return_value = mock_version_file
            
            version = _get_framework_version()
            
            assert version == "1.0.0"


class TestErrorHandling:
    """Test suite for error handling utilities."""
    
    def test_handle_service_errors_connection(self):
        """Test handling connection errors."""
        @handle_service_errors
        def test_func():
            raise ConnectionError("Connection failed")
        
        with patch('claude_pm.cli.cli_utils.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                test_func()
            
            assert exc_info.value.code == 1
            mock_console.print.assert_called()
            call_args = str(mock_console.print.call_args)
            assert "Connection error" in call_args
    
    def test_handle_service_errors_file_not_found(self):
        """Test handling file not found errors."""
        @handle_service_errors
        def test_func():
            raise FileNotFoundError("File missing")
        
        with patch('claude_pm.cli.cli_utils.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                test_func()
            
            assert exc_info.value.code == 1
            assert "File not found" in str(mock_console.print.call_args)
    
    def test_handle_service_errors_permission(self):
        """Test handling permission errors."""
        @handle_service_errors
        def test_func():
            raise PermissionError("Access denied")
        
        with patch('claude_pm.cli.cli_utils.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                test_func()
            
            assert exc_info.value.code == 1
            assert "Permission denied" in str(mock_console.print.call_args)


class TestProjectValidation:
    """Test suite for project validation utilities."""
    
    def test_validate_project_name_valid(self):
        """Test validating valid project names."""
        assert validate_project_name("my-project") is True
        assert validate_project_name("my_project") is True
        assert validate_project_name("project123") is True
        assert validate_project_name("MyProject") is True
    
    def test_validate_project_name_invalid(self):
        """Test validating invalid project names."""
        assert validate_project_name("") is False
        assert validate_project_name("my project") is False  # spaces
        assert validate_project_name("a" * 101) is False  # too long
        assert validate_project_name("project@123") is False  # special chars
        assert validate_project_name(None) is False


class TestFormattingFunctions:
    """Test suite for formatting functions."""
    
    def test_format_duration(self):
        """Test duration formatting."""
        assert format_duration(0.5) == "500ms"
        assert format_duration(1.5) == "1.5s"
        assert format_duration(65.5) == "1.1m"
        assert format_duration(3665.5) == "1.0h"
    
    def test_truncate_string(self):
        """Test string truncation."""
        assert truncate_string("short", 10) == "short"
        assert truncate_string("this is a very long string", 10) == "this is..."
        assert truncate_string("exact", 5) == "exact"
        assert truncate_string("toolong", 5) == "to..."
    
    def test_format_file_size(self):
        """Test file size formatting."""
        assert format_file_size(100) == "100.0B"
        assert format_file_size(1024) == "1.0KB"
        assert format_file_size(1024 * 1024) == "1.0MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.0GB"
    
    def test_safe_json_loads(self):
        """Test safe JSON loading."""
        assert safe_json_loads('{"key": "value"}') == {"key": "value"}
        assert safe_json_loads('invalid json', default={}) == {}
        assert safe_json_loads(None, default=[]) == []


class TestCLIContext:
    """Test suite for CLIContext class."""
    
    def test_cli_context_basic(self):
        """Test basic CLI context functionality."""
        with patch('claude_pm.cli.cli_utils.get_framework_config') as mock_config:
            mock_config.return_value = {'test': 'config'}
            
            with CLIContext() as ctx:
                assert ctx.start_time is not None
                assert ctx.config == {'test': 'config'}
                assert ctx.verbose is False
    
    def test_cli_context_verbose_timing(self):
        """Test CLI context with verbose timing."""
        with patch('claude_pm.cli.cli_utils.console') as mock_console:
            with patch('claude_pm.cli.cli_utils.get_framework_config'):
                ctx = CLIContext()
                ctx.verbose = True
                
                with ctx:
                    time.sleep(0.01)
                
                # Should print timing info
                mock_console.print.assert_called()
                call_args = str(mock_console.print.call_args)
                assert "Operation completed" in call_args


class TestConfigFileOperations:
    """Test suite for config file operations."""
    
    def test_load_config_file_json(self):
        """Test loading JSON config file."""
        with patch('claude_pm.cli.cli_utils.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            
            with patch('builtins.open', mock_open(read_data='{"key": "value"}')):
                config = load_config_file('config.json')
                assert config == {'key': 'value'}
    
    def test_load_config_file_yaml(self):
        """Test loading YAML config file."""
        with patch('claude_pm.cli.cli_utils.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            
            with patch('builtins.open', mock_open(read_data='key: value')):
                with patch('yaml.safe_load', return_value={'key': 'value'}):
                    config = load_config_file('config.yaml')
                    assert config == {'key': 'value'}
    
    def test_load_config_file_not_found(self):
        """Test loading non-existent config file."""
        with patch('claude_pm.cli.cli_utils.Path') as mock_path:
            mock_path.return_value.exists.return_value = False
            
            config = load_config_file('missing.json')
            assert config == {}
    
    def test_save_config_file(self):
        """Test saving config file."""
        config = {'key': 'value'}
        
        with patch('claude_pm.cli.cli_utils.Path') as mock_path:
            mock_path.return_value.parent.mkdir = Mock()
            
            with patch('builtins.open', mock_open()) as mock_file:
                save_config_file(config, 'config.json')
                
                mock_file.assert_called_once_with('config.json', 'w')
                handle = mock_file()
                written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
                assert 'key' in written_data
                assert 'value' in written_data


class TestDependencyAndSystemInfo:
    """Test suite for dependency and system info functions."""
    
    def test_check_dependency_exists(self):
        """Test checking existing dependency."""
        with patch('importlib.import_module') as mock_import:
            result = check_dependency('click')
            
            assert result is True
            mock_import.assert_called_once_with('click')
    
    def test_check_dependency_missing(self):
        """Test checking missing dependency."""
        with patch('importlib.import_module', side_effect=ImportError):
            result = check_dependency('missing_package')
            
            assert result is False
    
    def test_get_system_info(self):
        """Test getting system information."""
        with patch('platform.platform', return_value='Test Platform'):
            with patch('claude_pm.cli.cli_utils.get_claude_pm_path', return_value=Path('/claude/path')):
                with patch('claude_pm.cli.cli_utils.get_managed_path', return_value=Path('/managed/path')):
                    info = get_system_info()
                    
                    assert info['platform'] == 'Test Platform'
                    assert info['python_version'] == sys.version
                    assert info['framework_path'] == '/claude/path'
                    assert info['managed_path'] == '/managed/path'


class TestCommonOptions:
    """Test suite for common CLI options."""
    
    def test_common_options_decorator(self):
        """Test common options decorator."""
        @common_options
        def test_command(verbose, config):
            return f"verbose={verbose}, config={config}"
        
        # Check that options were added
        assert any(opt.name == 'verbose' for opt in test_command.params)
        assert any(opt.name == 'config' for opt in test_command.params)
    
    def test_common_options_with_model_decorator(self):
        """Test common options with model decorator."""
        @common_options_with_model
        def test_command(verbose, config, model):
            return f"verbose={verbose}, config={config}, model={model}"
        
        # Check that all options were added
        assert any(opt.name == 'verbose' for opt in test_command.params)
        assert any(opt.name == 'config' for opt in test_command.params)
        assert any(opt.name == 'model' for opt in test_command.params)


# Import for mock_open
from unittest.mock import mock_open