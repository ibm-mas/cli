"""Conftest for mirror tests.

Automatically applies the 'mirror' marker to all tests in this directory and subdirectories.
"""

import pytest
from pathlib import Path


def pytest_collection_modifyitems(config, items):
    """Auto-apply mirror marker to all tests in this directory."""
    mirror_dir = Path(__file__).parent
    for item in items:
        item_path = Path(item.fspath)
        if mirror_dir in item_path.parents or item_path.parent == mirror_dir:
            item.add_marker(pytest.mark.mirror)


# Made with Bob
