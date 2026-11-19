# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Pilot test configuration: auto-apply the pilot marker to every test here.

The marker is applied via a collection hook rather than per-file pytestmark
so it can never drift out of sync with the directory, and ``-m "not pilot"``
gives a fast local loop without the live-UI tests.
"""

import pytest
from pathlib import Path


def pytest_collection_modifyitems(config, items):
    """Tag every test collected under tests/pilot with the pilot marker.

    The hook receives every item in the session (conftest hooks are not
    scoped to their directory), so guard on the item's path -- the same
    approach as the other marker conftests -- to avoid leaking the pilot
    marker to unit and integration tests.
    """
    pilot_dir = Path(__file__).parent
    for item in items:
        item_path = Path(item.fspath)
        if pilot_dir in item_path.parents or item_path.parent == pilot_dir:
            item.add_marker(pytest.mark.pilot)
