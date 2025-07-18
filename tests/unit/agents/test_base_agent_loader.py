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
        mock_cache.get.assert_called_once_with(BASE_AGENT_CACHE_KEY)
        mock_cache.set.assert_not_called()
    
    @patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance')
    @patch('claude_pm.agents.base_agent_loader.BASE_AGENT_FILE')
    def test_load_from_file_when_not_cached(self, mock_file, mock_cache_class):
        """Test loading from file when not in cache."""
        # Setup
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = "base agent content from file"
        
        # Execute
        result = load_base_agent_instructions(force_reload=False)
        
        # Assert
        assert result == "base agent content from file"
        mock_cache.get.assert_called_once_with(BASE_AGENT_CACHE_KEY)
        mock_cache.set.assert_called_once_with(
            BASE_AGENT_CACHE_KEY, 
            "base agent content from file", 
            ttl=3600
        )
        mock_file.read_text.assert_called_once_with(encoding='utf-8')
    
    @patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance')
    @patch('claude_pm.agents.base_agent_loader.BASE_AGENT_FILE')
    def test_force_reload_bypasses_cache(self, mock_file, mock_cache_class):
        """Test force reload bypasses cache."""
        # Setup
        mock_cache = Mock()
        mock_cache_class.return_value = mock_cache
        
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = "fresh content"
        
        # Execute
        result = load_base_agent_instructions(force_reload=True)
        
        # Assert
        assert result == "fresh content"
        mock_cache.get.assert_not_called()
        mock_cache.set.assert_called_once_with(BASE_AGENT_CACHE_KEY, "fresh content", ttl=3600)
    
    @patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance')
    @patch('claude_pm.agents.base_agent_loader.BASE_AGENT_FILE')
    def test_returns_none_when_file_not_found(self, mock_file, mock_cache_class):
        """Test returns None when file doesn't exist."""
        # Setup
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_file.exists.return_value = False
        
        # Execute
        result = load_base_agent_instructions(force_reload=False)
        
        # Assert
        assert result is None
        mock_file.read_text.assert_not_called()
        mock_cache.set.assert_not_called()
    
    @patch('claude_pm.agents.base_agent_loader.SharedPromptCache.get_instance')
    @patch('claude_pm.agents.base_agent_loader.BASE_AGENT_FILE')
    def test_handles_read_error_gracefully(self, mock_file, mock_cache_class):
        """Test handles file read errors gracefully."""
        # Setup
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache_class.return_value = mock_cache
        
        mock_file.exists.return_value = True
        mock_file.read_text.side_effect = IOError("Permission denied")
        
        # Execute
        result = load_base_agent_instructions(force_reload=False)
        
        # Assert
        assert result is None
        mock_cache.set.assert_not_called()


class TestPrependBaseInstructions:
    """Test prepend_base_instructions function."""
    
    @patch('claude_pm.agents.base_agent_loader.load_base_agent_instructions')
    def test_prepends_base_to_agent_prompt(self, mock_load):
        """Test successfully prepends base instructions."""
        # Setup
        mock_load.return_value = "Base instructions"
        agent_prompt = "Agent specific instructions"
        
        # Execute
        result = prepend_base_instructions(agent_prompt)
        
        # Assert
        expected = "Base instructions\n\n---\n\nAgent specific instructions"
        assert result == expected
        mock_load.assert_called_once()
    
    @patch('claude_pm.agents.base_agent_loader.load_base_agent_instructions')
    def test_custom_separator(self, mock_load):
        """Test using custom separator."""
        # Setup
        mock_load.return_value = "Base instructions"
        agent_prompt = "Agent specific instructions"
        separator = "\n===\n"
        
        # Execute
        result = prepend_base_instructions(agent_prompt, separator=separator)
        
        # Assert
        expected = "Base instructions\n===\nAgent specific instructions"
        assert result == expected
    
    @patch('claude_pm.agents.base_agent_loader.load_base_agent_instructions')
    def test_returns_original_when_no_base(self, mock_load):
        """Test returns original prompt when no base instructions."""
        # Setup
        mock_load.return_value = None
        agent_prompt = "Agent specific instructions"
        
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
        mock_cache.invalidate.assert_called_once_with(BASE_AGENT_CACHE_KEY)
    
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