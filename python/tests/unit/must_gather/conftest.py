"""Shared fixtures and configuration for must_gather unit tests."""

import pytest
from pathlib import Path


def pytest_collection_modifyitems(config, items):
    """Automatically add 'must-gather' marker to all tests in this directory."""
    must_gather_dir = Path(__file__).parent
    for item in items:
        item_path = Path(item.fspath)
        if must_gather_dir in item_path.parents or item_path.parent == must_gather_dir:
            item.add_marker(pytest.mark.must_gather)


# Made with Bob
