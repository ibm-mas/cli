# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Conftest for upgrade tests.

Automatically applies the 'upgrade' marker to all tests in this directory and subdirectories.
"""

import pytest
from pathlib import Path


def pytest_collection_modifyitems(config, items):
    """Auto-apply upgrade marker to all tests in this directory."""
    upgrade_dir = Path(__file__).parent
    for item in items:
        item_path = Path(item.fspath)
        if upgrade_dir in item_path.parents or item_path.parent == upgrade_dir:
            item.add_marker(pytest.mark.upgrade)


# Made with Bob
