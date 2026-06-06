"""Conftest for integration tests.

Automatically applies the 'integration' marker to all tests in this directory and subdirectories.

Note: Logging mock is provided by the root conftest.py and applies to all tests automatically.
"""

import pytest
from pathlib import Path


def pytest_collection_modifyitems(config, items):
    """Auto-apply integration marker to all tests in this directory."""
    integration_dir = Path(__file__).parent
    for item in items:
        item_path = Path(item.fspath)
        if integration_dir in item_path.parents or item_path.parent == integration_dir:
            item.add_marker(pytest.mark.integration)


# Made with Bob
