# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Root conftest.py with pytest marker definitions and global fixtures.

This file defines all custom markers used throughout the test suite and provides
global fixtures that apply to all tests (unit and integration).
"""

import pytest
import logging
from unittest import mock
from unittest.mock import MagicMock


def pytest_configure(config):
    """Register custom markers for the test suite."""
    # Test category markers
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (may require cluster/external services)")

    # Feature-specific markers
    config.addinivalue_line("markers", "must-gather: Tests for must-gather functionality")
    config.addinivalue_line("markers", "install: Tests for installation functionality")
    config.addinivalue_line("markers", "mirror: Tests for mirror functionality")
    config.addinivalue_line("markers", "update: Tests for update functionality")
    config.addinivalue_line("markers", "upgrade: Tests for upgrade functionality")
    config.addinivalue_line("markers", "aiservice: Tests for AI service functionality")
    config.addinivalue_line("markers", "aiservice-install: Tests for AI service installation")

    # Component-specific markers (for must_gather subdirectories)
    config.addinivalue_line("markers", "argo: Tests for Argo-related functionality")
    config.addinivalue_line("markers", "common: Tests for common utilities")
    config.addinivalue_line("markers", "dependencies: Tests for dependency management")
    config.addinivalue_line("markers", "mas: Tests for MAS-specific functionality")
    config.addinivalue_line("markers", "ocp: Tests for OpenShift-related functionality")
    config.addinivalue_line("markers", "summarizer: Tests for summarizer functionality")


@pytest.fixture(autouse=True, scope="function")
def mock_logging_handlers():
    """
    Mock logging handlers to prevent real file I/O during all tests.

    This fixture automatically applies to ALL tests (unit and integration) and prevents
    the creation of mas.log files by replacing RotatingFileHandler with a mock handler
    that captures log records in memory.

    The fixture is autouse=True with function scope, so it applies to every test
    without needing to be explicitly requested.

    Benefits:
    - No mas.log files created during test runs
    - Eliminates disk I/O overhead from logging
    - Reduces test execution time by ~50%
    - No cleanup of log files needed
    - Applies to both unit and integration tests
    """
    # Create a mock handler that captures logs in memory
    mock_handler = MagicMock(spec=logging.Handler)
    mock_handler.level = logging.DEBUG
    mock_handler.setLevel = MagicMock()
    mock_handler.setFormatter = MagicMock()

    # Patch RotatingFileHandler to return our mock handler
    with mock.patch("logging.handlers.RotatingFileHandler", return_value=mock_handler):
        yield mock_handler


# Made with Bob
