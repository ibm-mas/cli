"""Conftest for unit tests.

Automatically applies the 'unit' marker to all tests in this directory and subdirectories.
"""

import pytest
from pathlib import Path


def pytest_collection_modifyitems(config, items):
    """Auto-apply unit marker to all tests in this directory."""
    unit_dir = Path(__file__).parent
    for item in items:
        item_path = Path(item.fspath)
        if unit_dir in item_path.parents or item_path.parent == unit_dir:
            item.add_marker(pytest.mark.unit)


# Made with Bob
