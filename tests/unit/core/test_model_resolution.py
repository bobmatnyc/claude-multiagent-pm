#!/usr/bin/env python3
"""
Test Suite for Model Resolution Functionality
===========================================

Comprehensive test suite for the _resolve_model_selection function including:
- Empty string validation bug fix tests
- Whitespace handling tests
- Valid model resolution tests
- Alias resolution tests
- Partial match tests
- Edge case handling tests
"""

import sys
from pathlib import Path
from typing import Optional

import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude_pm.cli import _resolve_model_selection, get_available_models
from claude_pm.services.model_selector import ModelType


class TestModelResolutionEmptyStringFix:
    """Test the critical empty string validation bug fix."""

    @pytest.mark.unit
    def test_empty_string_returns_none(self):
        """Test that empty string returns None."""
        result = _resolve_model_selection("")
        assert result is None

    @pytest.mark.unit
    def test_whitespace_only_spaces_returns_none(self):
        """Test that spaces-only input returns None."""
        result = _resolve_model_selection("   ")
        assert result is None

    @pytest.mark.unit
    def test_whitespace_only_tabs_returns_none(self):
        """Test that tabs-only input returns None."""
        result = _resolve_model_selection("\t")
        assert result is None

    @pytest.mark.unit
    def test_whitespace_only_newlines_returns_none(self):
        """Test that newlines-only input returns None."""
        result = _resolve_model_selection("\n")
        assert result is None

    @pytest.mark.unit
    def test_whitespace_mixed_returns_none(self):
        """Test that mixed whitespace returns None."""
        result = _resolve_model_selection(" \t\n ")
        assert result is None

    @pytest.mark.unit
    def test_whitespace_only_carriage_return_returns_none(self):
        """Test that carriage return only input returns None."""
        result = _resolve_model_selection("\r")
        assert result is None

    @pytest.mark.unit
    def test_whitespace_complex_mix_returns_none(self):
        """Test that complex whitespace mix returns None."""
        result = _resolve_model_selection(" \t\n\r \t ")
        assert result is None

    @pytest.mark.unit
    def test_none_input_returns_none(self):
        """Test that None input returns None."""
        result = _resolve_model_selection(None)
        assert result is None


class TestModelResolutionValidInputs:
    """Test valid model input resolution."""

    @pytest.mark.unit
    def test_sonnet_alias_resolution(self):
        """Test 'sonnet' alias resolves to Claude Sonnet 4."""
        result = _resolve_model_selection("sonnet")
        assert result == ModelType.SONNET_4.value
        assert "claude-sonnet-4" in result

    @pytest.mark.unit
    def test_opus_alias_resolution(self):
        """Test 'opus' alias resolves to Claude 4 Opus."""
        result = _resolve_model_selection("opus")
        assert result == ModelType.OPUS_4.value
        assert "claude-4-opus" in result

    @pytest.mark.unit
    def test_haiku_alias_resolution(self):
        """Test 'haiku' alias resolves to Claude 3 Haiku."""
        result = _resolve_model_selection("haiku")
        assert result == ModelType.HAIKU.value
        assert "claude-3-haiku" in result

    @pytest.mark.unit
    def test_sonnet4_alias_resolution(self):
        """Test 'sonnet4' alias resolves to Claude Sonnet 4."""
        result = _resolve_model_selection("sonnet4")
        assert result == ModelType.SONNET_4.value

    @pytest.mark.unit
    def test_opus4_alias_resolution(self):
        """Test 'opus4' alias resolves to Claude 4 Opus."""
        result = _resolve_model_selection("opus4")
        assert result == ModelType.OPUS_4.value

    @pytest.mark.unit
    def test_sonnet3_alias_resolution(self):
        """Test 'sonnet3' alias resolves to Claude 3 Sonnet."""
        result = _resolve_model_selection("sonnet3")
        assert result == ModelType.SONNET.value

    @pytest.mark.unit
    def test_opus3_alias_resolution(self):
        """Test 'opus3' alias resolves to Claude 3 Opus."""
        result = _resolve_model_selection("opus3")
        assert result == ModelType.OPUS.value


class TestModelResolutionCaseInsensitive:
    """Test case-insensitive model resolution."""

    @pytest.mark.unit
    def test_uppercase_sonnet_resolution(self):
        """Test uppercase 'SONNET' resolves correctly."""
        result = _resolve_model_selection("SONNET")
        assert result == ModelType.SONNET_4.value

    @pytest.mark.unit
    def test_mixed_case_opus_resolution(self):
        """Test mixed case 'OpUs' resolves correctly."""
        result = _resolve_model_selection("OpUs")
        assert result == ModelType.OPUS_4.value

    @pytest.mark.unit
    def test_lowercase_haiku_resolution(self):
        """Test lowercase 'haiku' resolves correctly."""
        result = _resolve_model_selection("haiku")
        assert result == ModelType.HAIKU.value


class TestModelResolutionWhitespaceHandling:
    """Test proper whitespace handling for valid inputs."""

    @pytest.mark.unit
    def test_sonnet_with_leading_spaces(self):
        """Test 'sonnet' with leading spaces resolves correctly."""
        result = _resolve_model_selection("  sonnet")
        assert result == ModelType.SONNET_4.value

    @pytest.mark.unit
    def test_opus_with_trailing_spaces(self):
        """Test 'opus' with trailing spaces resolves correctly."""
        result = _resolve_model_selection("opus  ")
        assert result == ModelType.OPUS_4.value

    @pytest.mark.unit
    def test_haiku_with_surrounding_spaces(self):
        """Test 'haiku' with surrounding spaces resolves correctly."""
        result = _resolve_model_selection("  haiku  ")
        assert result == ModelType.HAIKU.value

    @pytest.mark.unit
    def test_sonnet_with_tabs(self):
        """Test 'sonnet' with tabs resolves correctly."""
        result = _resolve_model_selection("\tsonnet\t")
        assert result == ModelType.SONNET_4.value

    @pytest.mark.unit
    def test_opus_with_newlines(self):
        """Test 'opus' with newlines resolves correctly."""
        result = _resolve_model_selection("\nopus\n")
        assert result == ModelType.OPUS_4.value


class TestModelResolutionDirectModelIds:
    """Test direct model ID resolution."""

    @pytest.mark.unit
    def test_full_sonnet4_model_id(self):
        """Test full Claude Sonnet 4 model ID resolves correctly."""
        model_id = ModelType.SONNET_4.value
        result = _resolve_model_selection(model_id)
        assert result == model_id

    @pytest.mark.unit
    def test_full_opus4_model_id(self):
        """Test full Claude 4 Opus model ID resolves correctly."""
        model_id = ModelType.OPUS_4.value
        result = _resolve_model_selection(model_id)
        assert result == model_id

    @pytest.mark.unit
    def test_full_haiku_model_id(self):
        """Test full Claude 3 Haiku model ID resolves correctly."""
        model_id = ModelType.HAIKU.value
        result = _resolve_model_selection(model_id)
        assert result == model_id


class TestModelResolutionPartialMatches:
    """Test partial match functionality."""

    @pytest.mark.unit
    def test_partial_claude_4_opus_match(self):
        """Test partial match for 'claude-4-opus'."""
        result = _resolve_model_selection("claude-4-opus")
        assert result == ModelType.OPUS_4.value

    @pytest.mark.unit
    def test_partial_sonnet_match(self):
        """Test partial match for 'sonnet-4'."""
        result = _resolve_model_selection("sonnet-4")
        assert result == ModelType.SONNET_4.value

    @pytest.mark.unit
    def test_partial_haiku_match(self):
        """Test partial match for '3-haiku'."""
        result = _resolve_model_selection("3-haiku")
        assert result == ModelType.HAIKU.value


class TestModelResolutionInvalidInputs:
    """Test invalid input handling."""

    @pytest.mark.unit
    def test_invalid_model_name_returns_none(self):
        """Test invalid model name returns None."""
        result = _resolve_model_selection("invalid-model")
        assert result is None

    @pytest.mark.unit
    def test_random_string_returns_none(self):
        """Test random string returns None."""
        result = _resolve_model_selection("random-xyz-123")
        assert result is None

    @pytest.mark.unit
    def test_numeric_string_returns_none(self):
        """Test numeric string returns None."""
        result = _resolve_model_selection("12345")
        assert result is None

    @pytest.mark.unit
    def test_special_characters_returns_none(self):
        """Test special characters return None."""
        result = _resolve_model_selection("@#$%^&*()")
        assert result is None


class TestModelResolutionEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_very_long_string_returns_none(self):
        """Test very long string returns None."""
        long_string = "a" * 1000
        result = _resolve_model_selection(long_string)
        assert result is None

    @pytest.mark.unit
    def test_single_character_returns_none(self):
        """Test single character returns None."""
        result = _resolve_model_selection("a")
        assert result is None

    @pytest.mark.unit
    def test_unicode_characters_returns_none(self):
        """Test unicode characters return None."""
        result = _resolve_model_selection("🤖")
        assert result is None

    @pytest.mark.unit
    def test_partial_alias_match_returns_none(self):
        """Test partial alias match that shouldn't work returns None."""
        result = _resolve_model_selection("sonn")  # partial of "sonnet"
        assert result is None

    @pytest.mark.unit
    def test_similar_but_invalid_name_returns_none(self):
        """Test similar but invalid name returns None."""
        result = _resolve_model_selection("sonnets")  # plural
        assert result is None


class TestModelResolutionBackwardCompatibility:
    """Test backward compatibility with existing functionality."""

    @pytest.mark.unit
    def test_get_available_models_includes_all_aliases(self):
        """Test get_available_models includes all expected aliases."""
        available_models = get_available_models()
        
        expected_aliases = {
            'sonnet', 'sonnet4', 'opus', 'opus4', 
            'haiku', 'sonnet3', 'opus3'
        }
        
        assert all(alias in available_models for alias in expected_aliases)

    @pytest.mark.unit
    def test_all_available_models_resolve_correctly(self):
        """Test all available models resolve to valid ModelType values."""
        available_models = get_available_models()
        
        for alias, expected_model_id in available_models.items():
            result = _resolve_model_selection(alias)
            assert result == expected_model_id
            assert result is not None


class TestModelResolutionRegressionPrevention:
    """Test prevention of regression to the original bug."""

    @pytest.mark.unit
    def test_regression_whitespace_does_not_match_first_model(self):
        """Test that whitespace doesn't match the first model (regression test)."""
        # Get the first model type to ensure we don't accidentally match it
        first_model = next(iter(ModelType)).value
        
        # Test that whitespace inputs don't match the first model
        whitespace_inputs = ["   ", "\t", "\n", " \t\n ", "\r", ""]
        
        for whitespace_input in whitespace_inputs:
            result = _resolve_model_selection(whitespace_input)
            assert result is None, f"Whitespace input '{repr(whitespace_input)}' should not resolve to any model"
            assert result != first_model, f"Whitespace input '{repr(whitespace_input)}' incorrectly resolved to first model"

    @pytest.mark.unit
    def test_regression_empty_string_not_contained_in_all_strings(self):
        """Test the core fix: empty string after strip() doesn't match all models."""
        # This test specifically validates the fix for the partial match logic
        
        # Simulate the problematic inputs
        problematic_inputs = ["   ", "\t", "\n"]
        
        for input_str in problematic_inputs:
            normalized = input_str.lower().strip()
            assert normalized == "", f"Input '{repr(input_str)}' should normalize to empty string"
            
            # The fix should catch this before it reaches the partial match logic
            result = _resolve_model_selection(input_str)
            assert result is None, f"Input '{repr(input_str)}' should return None after fix"

    @pytest.mark.unit
    def test_regression_valid_inputs_still_work_after_fix(self):
        """Test that valid inputs still work correctly after the fix."""
        # Ensure the fix doesn't break valid functionality
        test_cases = [
            ("sonnet", ModelType.SONNET_4.value),
            ("opus", ModelType.OPUS_4.value),
            ("haiku", ModelType.HAIKU.value),
            ("  sonnet  ", ModelType.SONNET_4.value),  # with whitespace
            ("OPUS", ModelType.OPUS_4.value),  # case insensitive
        ]
        
        for input_str, expected in test_cases:
            result = _resolve_model_selection(input_str)
            assert result == expected, f"Valid input '{input_str}' should resolve to '{expected}', got '{result}'"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])