#!/usr/bin/env python3
"""
Unit tests for base_agent_loader.py
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from claude_pm.agents.base_agent_loader import (
    load_base_agent_instructions,
    prepend_base_instructions,
    clear_base_agent_cache,
    get_base_agent_path,
    validate_base_agent_file,
    BASE_AGENT_CACHE_KEY,
    BASE_AGENT_FILE
)


class TestLoadBaseAgentInstructions:
    """Test load_base_agent_instructions function."""
    
    @patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance')
    def test_load_from_cache(self, mock_cache_class):
        """Test loading from cache when available."""
        # Setup
        mock_cache = Mock()
        mock_cache.get.return_value = "cached base instructions"
        mock_cache_class.return_value = mock_cache
        
        # Execute
        result = load_base_agent_instructions(force_reload=False)
        
        # Assert
        assert result == "cached base instructions"
        # Updated to match new cache key format with :normal suffix
        mock_cache.get.assert_called_once_with(f"{BASE_AGENT_CACHE_KEY}:normal")
        mock_cache.set.assert_not_called()
    
    @patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance')
    @patch('claude_pm.agents.base_agent_loader._get_base_agent_file')
    def test_load_from_file_when_not_cached(self, mock_get_file, mock_cache_class):
        """Test loading from file when not in cache."""
        # Setup
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = "base agent content from file"
        mock_get_file.return_value = mock_file
        
        # Execute
        result = load_base_agent_instructions(force_reload=False)
        
        # Assert
        assert result == "base agent content from file"
        # Updated to match new cache key format with :normal suffix
        mock_cache.get.assert_called_once_with(f"{BASE_AGENT_CACHE_KEY}:normal")
        mock_cache.set.assert_called_once_with(
            f"{BASE_AGENT_CACHE_KEY}:normal", 
            "base agent content from file", 
            ttl=3600
        )
        mock_file.read_text.assert_called_once_with(encoding='utf-8')
    
    @patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance')
    @patch('claude_pm.agents.base_agent_loader._get_base_agent_file')
    def test_force_reload_bypasses_cache(self, mock_get_file, mock_cache_class):
        """Test force reload bypasses cache."""
        # Setup
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = "fresh content"
        mock_get_file.return_value = mock_file
        
        # Execute
        result = load_base_agent_instructions(force_reload=True)
        
        # Assert
        assert result == "fresh content"
        mock_cache.get.assert_not_called()
        # Updated to match new cache key format with :normal suffix
        mock_cache.set.assert_called_once_with(f"{BASE_AGENT_CACHE_KEY}:normal", "fresh content", ttl=3600)
    
    @patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance')
    @patch('claude_pm.agents.base_agent_loader._get_base_agent_file')
    def test_returns_none_when_file_not_found(self, mock_get_file, mock_cache_class):
        """Test returns None when file doesn't exist."""
        # Setup
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_file = Mock()
        mock_file.exists.return_value = False
        mock_get_file.return_value = mock_file
        
        # Execute
        result = load_base_agent_instructions(force_reload=False)
        
        # Assert
        assert result is None
        mock_file.read_text.assert_not_called()
        mock_cache.set.assert_not_called()
    
    @patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance')
    @patch('claude_pm.agents.base_agent_loader._get_base_agent_file')
    def test_handles_read_error_gracefully(self, mock_get_file, mock_cache_class):
        """Test handles file read errors gracefully."""
        # Setup
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_file.read_text.side_effect = IOError("Permission denied")
        mock_get_file.return_value = mock_file
        
        # Execute
        result = load_base_agent_instructions(force_reload=False)
        
        # Assert
        assert result is None
        mock_cache.set.assert_not_called()


class TestPrependBaseInstructions:
    """Test prepend_base_instructions function."""
    
    @patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance')
    def test_prepends_base_to_agent_prompt(self, mock_cache_class):
        """Test successfully prepends base instructions."""
        # Setup
        mock_cache = Mock()
        # Return None from cache to trigger file load
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        agent_prompt = "Agent specific instructions"
        
        # Mock the load_base_agent_instructions to return base content
        with patch('claude_pm.agents.base_agent_loader.load_base_agent_instructions') as mock_load:
            mock_load.return_value = "Base instructions"
            
            # Execute
            result = prepend_base_instructions(agent_prompt)
            
            # Assert
            # The function now returns base instructions prepended
            assert "Agent specific instructions" in result
            assert result.endswith("Agent specific instructions")
            # Should contain separator
            assert "---" in result
    
    @patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance')
    def test_custom_separator(self, mock_cache_class):
        """Test using custom separator."""
        # Setup
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        agent_prompt = "Agent specific instructions"
        separator = "\n===\n"
        
        with patch('claude_pm.agents.base_agent_loader.load_base_agent_instructions') as mock_load:
            mock_load.return_value = "Base instructions"
            
            # Execute
            result = prepend_base_instructions(agent_prompt, separator=separator)
            
            # Assert
            assert "Agent specific instructions" in result
            assert result.endswith("Agent specific instructions")
            # Should contain custom separator
            assert "===" in result
    
    @patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance')
    def test_returns_original_when_no_base(self, mock_cache_class):
        """Test returns original prompt when no base instructions."""
        # Setup
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        agent_prompt = "Agent specific instructions"
        
        with patch('claude_pm.agents.base_agent_loader.load_base_agent_instructions') as mock_load:
            mock_load.return_value = None
            
            # Execute
            result = prepend_base_instructions(agent_prompt)
            
            # Assert
            assert result == agent_prompt
            mock_load.assert_called_once()


class TestClearBaseAgentCache:
    """Test clear_base_agent_cache function."""
    
    @patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance')
    def test_clears_cache_successfully(self, mock_cache_class):
        """Test cache clearing succeeds."""
        # Setup
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        
        # Execute
        clear_base_agent_cache()
        
        # Assert
        # The function now clears multiple cache keys for all templates and modes
        # We should check that invalidate was called multiple times
        assert mock_cache.invalidate.call_count >= 2  # At least normal and test modes
    
    @patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance')
    def test_handles_cache_error(self, mock_cache_class):
        """Test handles cache clearing errors."""
        # Setup
        mock_cache = Mock()
        mock_cache.invalidate.side_effect = Exception("Cache error")
        mock_cache_class.return_value = mock_cache
        
        # Execute (should not raise)
        clear_base_agent_cache()
        
        # Assert
        mock_cache.invalidate.assert_called_once()


class TestGetBaseAgentPath:
    """Test get_base_agent_path function."""
    
    def test_returns_correct_path(self):
        """Test returns the BASE_AGENT_FILE path."""
        result = get_base_agent_path()
        assert result == BASE_AGENT_FILE
        assert isinstance(result, Path)


class TestValidateBaseAgentFile:
    """Test validate_base_agent_file function."""
    
    @patch('claude_pm.agents.base_agent_loader.BASE_AGENT_FILE')
    def test_valid_file(self, mock_file):
        """Test validation passes for valid file."""
        # Setup
        mock_file.exists.return_value = True
        mock_file.is_file.return_value = True
        mock_file.read_text.return_value = "content"
        
        # Execute
        result = validate_base_agent_file()
        
        # Assert
        assert result is True
        mock_file.exists.assert_called_once()
        mock_file.is_file.assert_called_once()
        mock_file.read_text.assert_called_once_with(encoding='utf-8')
    
    @patch('claude_pm.agents.base_agent_loader.BASE_AGENT_FILE')
    def test_file_not_exists(self, mock_file):
        """Test validation fails when file doesn't exist."""
        # Setup
        mock_file.exists.return_value = False
        
        # Execute
        result = validate_base_agent_file()
        
        # Assert
        assert result is False
        mock_file.is_file.assert_not_called()
    
    @patch('claude_pm.agents.base_agent_loader.BASE_AGENT_FILE')
    def test_path_not_file(self, mock_file):
        """Test validation fails when path is not a file."""
        # Setup
        mock_file.exists.return_value = True
        mock_file.is_file.return_value = False
        
        # Execute
        result = validate_base_agent_file()
        
        # Assert
        assert result is False
        mock_file.read_text.assert_not_called()
    
    @patch('claude_pm.agents.base_agent_loader.BASE_AGENT_FILE')
    def test_file_not_readable(self, mock_file):
        """Test validation fails when file is not readable."""
        # Setup
        mock_file.exists.return_value = True
        mock_file.is_file.return_value = True
        mock_file.read_text.side_effect = PermissionError("Access denied")
        
        # Execute
        result = validate_base_agent_file()
        
        # Assert
        assert result is False


# Fixtures for integration tests
@pytest.fixture
def temp_base_agent_file(tmp_path):
    """Create a temporary base_agent.md file."""
    base_agent_content = """# Base Agent Instructions

## Core Principles
- Stay within your domain
- Provide operational insights

## Common Rules
- Be concise
- Handle errors gracefully
"""
    file_path = tmp_path / "base_agent.md"
    file_path.write_text(base_agent_content)
    return file_path


@pytest.fixture
def mock_base_agent_file(temp_base_agent_file, monkeypatch):
    """Mock BASE_AGENT_FILE to use temp file."""
    monkeypatch.setattr(
        'claude_pm.agents.base_agent_loader.BASE_AGENT_FILE',
        temp_base_agent_file
    )
    return temp_base_agent_file