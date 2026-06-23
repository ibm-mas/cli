# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Conftest for rollback tests.

Automatically applies the 'rollback' marker to all tests in this directory.
"""

import pytest
from pathlib import Path


def pytest_collection_modifyitems(config, items):
    """Auto-apply rollback marker to all tests in this directory."""
    rollback_dir = Path(__file__).parent
    for item in items:
        item_path = Path(item.fspath)
        if rollback_dir in item_path.parents or item_path.parent == rollback_dir:
            item.add_marker(pytest.mark.rollback)
