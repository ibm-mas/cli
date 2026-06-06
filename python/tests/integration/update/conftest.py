"""Conftest for update tests.

Automatically applies the 'update' marker to all tests in this directory and subdirectories.
"""

import pytest
from pathlib import Path


def pytest_collection_modifyitems(config, items):
    """Auto-apply update marker to all tests in this directory."""
    update_dir = Path(__file__).parent
    for item in items:
        item_path = Path(item.fspath)
        if update_dir in item_path.parents or item_path.parent == update_dir:
            item.add_marker(pytest.mark.update)


# Made with Bob
