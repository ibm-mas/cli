"""Conftest for aiservice_install tests.

Automatically applies the 'aiservice-install' marker to all tests in this directory and subdirectories.
"""

import pytest
from pathlib import Path


def pytest_collection_modifyitems(config, items):
    """Auto-apply aiservice-install marker to all tests in this directory."""
    aiservice_install_dir = Path(__file__).parent
    for item in items:
        item_path = Path(item.fspath)
        if aiservice_install_dir in item_path.parents or item_path.parent == aiservice_install_dir:
            item.add_marker(pytest.mark.aiservice_install)


# Made with Bob
