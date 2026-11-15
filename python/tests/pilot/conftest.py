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


def pytest_collection_modifyitems(items):
    """Tag every test collected under tests/pilot with the pilot marker."""
    for item in items:
        item.add_marker(pytest.mark.pilot)
