"""
Pytest configuration for E2E core tests
"""

import pytest
import os
import tempfile
import shutil


@pytest.fixture
def setup_and_teardown():
    """Basic setup and teardown for E2E tests."""
    # Setup
    original_cwd = os.getcwd()
    test_dir = tempfile.mkdtemp(prefix="e2e_test_core_")
    
    yield
    
    # Teardown
    os.chdir(original_cwd)
    shutil.rmtree(test_dir, ignore_errors=True)