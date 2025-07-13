"""
Unit tests for deployment_detector module

Tests the extracted deployment detection functionality from ISS-0085 Phase 2
modular architecture implementation.
"""

import pytest
import unittest.mock as mock
from pathlib import Path
import subprocess
import socket
import json

from claude_pm.modules.deployment_detector import (
    DeploymentDetector,
    detect_aitrackdown_info,
    detect_memory_manager_info,
    get_framework_version,
    detect_claude_md_version,
    display_directory_context
)


class TestDeploymentDetector:
    """Test cases for the DeploymentDetector class."""
    
    def test_initialization(self):
        """Test DeploymentDetector initialization."""
        detector = DeploymentDetector()
        assert detector.timeout == 3
        assert detector._cache == {}
        
        detector_custom = DeploymentDetector(timeout=5)
        assert detector_custom.timeout == 5
    
    def test_get_deployment_context(self):
        """Test deployment context detection."""
        detector = DeploymentDetector()
        context = detector._get_deployment_context()
        
        assert isinstance(context, dict)
        assert "deployment_dir" in context
        assert "working_dir" in context
    
    @mock.patch('claude_pm.modules.deployment_detector.detect_aitrackdown_info')
    @mock.patch('claude_pm.modules.deployment_detector.detect_memory_manager_info')
    @mock.patch('claude_pm.modules.deployment_detector.get_framework_version')
    @mock.patch('claude_pm.modules.deployment_detector.detect_claude_md_version')
    def test_get_full_environment_info(self, mock_claude_md, mock_framework, mock_memory, mock_aitrackdown):
        """Test comprehensive environment information gathering."""
        # Setup mocks
        mock_aitrackdown.return_value = "v1.0.0 (global)"
        mock_memory.return_value = "mem0AI v1.0.0 (active, 5 memories)"
        mock_framework.return_value = "0.6.0"
        mock_claude_md.return_value = "v0.6.0-001"
        
        detector = DeploymentDetector()
        info = detector.get_full_environment_info()
        
        assert isinstance(info, dict)
        assert "aitrackdown_info" in info
        assert "memory_manager_info" in info
        assert "framework_version" in info
        assert "claude_md_version" in info
        assert "deployment_context" in info
        
        # Verify function calls
        mock_aitrackdown.assert_called_once_with(timeout=3)
        mock_memory.assert_called_once_with(timeout=3)
        mock_framework.assert_called_once()
        mock_claude_md.assert_called_once()


class TestDetectAitrackdownInfo:
    """Test cases for AI-Trackdown detection."""
    
    @mock.patch('subprocess.run')
    def test_detect_global_aitrackdown_success(self, mock_run):
        """Test successful detection of global aitrackdown."""
        # Mock successful aitrackdown --version
        mock_run.side_effect = [
            mock.Mock(returncode=0, stdout="1.2.3"),  # aitrackdown --version
            mock.Mock(returncode=0, stdout="/usr/local/bin/aitrackdown")  # which aitrackdown
        ]
        
        result = detect_aitrackdown_info()
        assert result == "v1.2.3 (global (system))"
    
    @mock.patch('subprocess.run')
    def test_detect_nvm_deployment(self, mock_run):
        """Test detection of NVM-based deployment."""
        mock_run.side_effect = [
            mock.Mock(returncode=0, stdout="1.2.3"),
            mock.Mock(returncode=0, stdout="/Users/user/.nvm/versions/node/v20.19.0/bin/aitrackdown")
        ]
        
        result = detect_aitrackdown_info()
        assert result == "v1.2.3 (global (nvm))"
    
    @mock.patch('subprocess.run')
    def test_detect_framework_cli(self, mock_run):
        """Test detection of framework CLI."""
        # Mock failed global check, but framework CLI exists
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "aitrackdown"),  # Global fails
            mock.Mock(returncode=0, stdout="1.2.3")  # Framework CLI succeeds
        ]
        
        with mock.patch('pathlib.Path.exists', return_value=True):
            result = detect_aitrackdown_info()
            assert result == "v1.2.3 (framework CLI)"
    
    @mock.patch('subprocess.run')
    def test_detect_atd_alias(self, mock_run):
        """Test detection of atd alias as fallback."""
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "aitrackdown"),  # Global aitrackdown fails
            mock.Mock(returncode=0, stdout="1.2.3")  # atd succeeds
        ]
        
        with mock.patch('pathlib.Path.exists', return_value=False):
            result = detect_aitrackdown_info()
            assert result == "v1.2.3 (atd alias)"
    
    @mock.patch('subprocess.run')
    def test_not_found(self, mock_run):
        """Test when AI-Trackdown is not found."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        
        with mock.patch('pathlib.Path.exists', return_value=False):
            result = detect_aitrackdown_info()
            assert result == "not found"
    
    def test_timeout_parameter(self):
        """Test custom timeout parameter."""
        with mock.patch('subprocess.run') as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="1.0.0")
            
            detect_aitrackdown_info(timeout=5)
            # Check that the first call used the custom timeout
            first_call = mock_run.call_args_list[0]
            assert first_call[1]['timeout'] == 5


class TestDetectMemoryManagerInfo:
    """Test cases for memory manager detection."""
    
    @mock.patch('urllib.request.urlopen')
    @mock.patch('socket.socket')
    @mock.patch('subprocess.run')
    def test_active_service_with_memories(self, mock_run, mock_socket, mock_urlopen):
        """Test detection of active mem0AI service with memories."""
        # Mock successful mem0 version check
        mock_run.return_value = mock.Mock(returncode=0, stdout="1.0.0")
        
        # Mock successful socket connection
        mock_sock_instance = mock.Mock()
        mock_sock_instance.connect_ex.return_value = 0
        mock_socket.return_value = mock_sock_instance
        
        # Mock HTTP response with memory count
        mock_response = mock.Mock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"count": 42}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = detect_memory_manager_info()
        assert result == "mem0AI v1.0.0 (active, 42 memories)"
    
    @mock.patch('socket.socket')
    @mock.patch('subprocess.run')
    def test_inactive_service(self, mock_run, mock_socket):
        """Test detection when service is inactive."""
        # Mock successful mem0 version check
        mock_run.return_value = mock.Mock(returncode=0, stdout="1.0.0")
        
        # Mock failed socket connection
        mock_sock_instance = mock.Mock()
        mock_sock_instance.connect_ex.return_value = 1  # Connection failed
        mock_socket.return_value = mock_sock_instance
        
        result = detect_memory_manager_info()
        assert result == "mem0AI v1.0.0 (inactive)"
    
    @mock.patch('urllib.request.urlopen')
    @mock.patch('socket.socket')
    @mock.patch('subprocess.run')
    def test_no_mem0_package(self, mock_run, mock_socket, mock_urlopen):
        """Test when mem0 package is not installed."""
        # Mock failed mem0 import
        mock_run.side_effect = subprocess.CalledProcessError(1, "python3")
        
        # Mock active service but no package
        mock_sock_instance = mock.Mock()
        mock_sock_instance.connect_ex.return_value = 0
        mock_socket.return_value = mock_sock_instance
        
        # Mock HTTP response with memory count
        mock_response = mock.Mock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"count": 0}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = detect_memory_manager_info()
        assert result == "mem0AI not available (active, 0 memories)"


class TestGetFrameworkVersion:
    """Test cases for framework version detection."""
    
    @mock.patch('pathlib.Path.exists')
    @mock.patch('pathlib.Path.read_text')
    def test_version_file_exists(self, mock_read_text, mock_exists):
        """Test reading version from VERSION file."""
        mock_exists.return_value = True
        mock_read_text.return_value = "0.6.0\n"
        
        result = get_framework_version()
        assert result == "0.6.0"
    
    @mock.patch('pathlib.Path.exists')
    def test_version_file_missing_fallback_to_package(self, mock_exists):
        """Test fallback to package version when VERSION file is missing."""
        mock_exists.return_value = False
        
        with mock.patch('claude_pm.__version__', "0.5.0"):
            result = get_framework_version()
            assert result == "0.5.0"
    
    @mock.patch('pathlib.Path.exists')
    def test_error_fallback_to_unknown(self, mock_exists):
        """Test fallback to 'unknown' when all methods fail."""
        mock_exists.side_effect = Exception("File error")
        
        # Mock the entire claude_pm import to fail
        with mock.patch.dict('sys.modules', {'claude_pm': None}):
            result = get_framework_version()
            assert result == "unknown"


class TestDetectClaudeMdVersion:
    """Test cases for CLAUDE.md version detection."""
    
    @mock.patch('pathlib.Path.cwd')
    @mock.patch('pathlib.Path.exists')
    def test_claude_md_not_found(self, mock_exists, mock_cwd):
        """Test when CLAUDE.md file is not found."""
        mock_cwd.return_value = Path("/test")
        mock_exists.return_value = False
        
        result = detect_claude_md_version()
        assert result == "Not found"
    
    @mock.patch('claude_pm.modules.deployment_detector.get_framework_version')
    @mock.patch('builtins.open', mock.mock_open(read_data="CLAUDE_MD_VERSION: 0.6.0-001"))
    @mock.patch('pathlib.Path.cwd')
    @mock.patch('pathlib.Path.exists')
    def test_version_with_serial(self, mock_exists, mock_cwd, mock_get_version):
        """Test version detection with serial number format."""
        mock_cwd.return_value = Path("/test")
        mock_exists.return_value = True
        mock_get_version.return_value = "0.6.0"
        
        result = detect_claude_md_version()
        assert result == "v0.6.0-001"
    
    @mock.patch('claude_pm.modules.deployment_detector.get_framework_version')
    @mock.patch('builtins.open', mock.mock_open(read_data="CLAUDE_MD_VERSION: 0.6.0"))
    @mock.patch('pathlib.Path.cwd')
    @mock.patch('pathlib.Path.exists')
    def test_legacy_version_format(self, mock_exists, mock_cwd, mock_get_version):
        """Test legacy version format detection."""
        mock_cwd.return_value = Path("/test")
        mock_exists.return_value = True
        mock_get_version.return_value = "0.6.0"
        
        result = detect_claude_md_version()
        assert result == "v0.6.0 (Legacy format)"
    
    @mock.patch('builtins.open', mock.mock_open(read_data="No version info here"))
    @mock.patch('pathlib.Path.cwd')
    @mock.patch('pathlib.Path.exists')
    def test_no_version_detected(self, mock_exists, mock_cwd):
        """Test when file exists but no version is detected."""
        mock_cwd.return_value = Path("/test")
        mock_exists.return_value = True
        
        result = detect_claude_md_version()
        assert result == "Found (no version detected)"


class TestDisplayDirectoryContext:
    """Test cases for directory context display."""
    
    @mock.patch.dict('os.environ', {
        'CLAUDE_PM_DEPLOYMENT_DIR': '/test/deployment',
        'CLAUDE_PM_WORKING_DIR': '/test/working'
    })
    @mock.patch('claude_pm.modules.deployment_detector.detect_aitrackdown_info')
    @mock.patch('claude_pm.modules.deployment_detector.detect_memory_manager_info')
    @mock.patch('claude_pm.modules.deployment_detector.detect_claude_md_version')
    @mock.patch('claude_pm.modules.deployment_detector.console')
    def test_display_with_env_vars(self, mock_console, mock_claude_md, mock_memory, mock_aitrackdown):
        """Test display with environment variables set."""
        mock_aitrackdown.return_value = "v1.0.0 (global)"
        mock_memory.return_value = "mem0AI v1.0.0 (active)"
        mock_claude_md.return_value = "v0.6.0-001"
        
        display_directory_context()
        
        # Verify console.print was called with expected content
        assert mock_console.print.call_count >= 5  # At least 5 print calls expected
        
        # Check specific calls
        calls = [call[0][0] for call in mock_console.print.call_args_list]
        assert any("/test/deployment" in call for call in calls)
        assert any("/test/working" in call for call in calls)
    
    @mock.patch.dict('os.environ', {}, clear=True)
    @mock.patch('pathlib.Path.exists')
    @mock.patch('claude_pm.modules.deployment_detector.console')
    def test_display_fallback_detection(self, mock_console, mock_exists):
        """Test fallback directory detection when env vars are not set."""
        mock_exists.return_value = True  # Framework structure exists
        
        with mock.patch('claude_pm.modules.deployment_detector.detect_aitrackdown_info', return_value="not found"), \
             mock.patch('claude_pm.modules.deployment_detector.detect_memory_manager_info', return_value="inactive"), \
             mock.patch('claude_pm.modules.deployment_detector.detect_claude_md_version', return_value="Not found"):
            
            display_directory_context()
            
            # Should not raise an exception and should call console.print
            assert mock_console.print.called


if __name__ == "__main__":
    pytest.main([__file__])