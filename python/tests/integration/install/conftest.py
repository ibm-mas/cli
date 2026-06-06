"""Conftest for install tests.

Automatically applies the 'install' marker to all tests in this directory and subdirectories.
"""

import pytest
from pathlib import Path


def pytest_collection_modifyitems(config, items):
    """Auto-apply install marker to all tests in this directory."""
    install_dir = Path(__file__).parent
    for item in items:
        item_path = Path(item.fspath)
        if install_dir in item_path.parents or item_path.parent == install_dir:
            item.add_marker(pytest.mark.install)


# Made with Bob
