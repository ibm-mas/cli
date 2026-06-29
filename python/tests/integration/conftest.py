# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Conftest for integration tests.

Automatically applies the 'integration' marker to all tests in this directory and subdirectories.

Note: Logging mock is provided by the root conftest.py and applies to all tests automatically.
"""

import pytest
from pathlib import Path
from unittest import mock


def pytest_collection_modifyitems(config, items):
    """Auto-apply integration marker to all tests in this directory."""
    integration_dir = Path(__file__).parent
    for item in items:
        item_path = Path(item.fspath)
        if integration_dir in item_path.parents or item_path.parent == integration_dir:
            item.add_marker(pytest.mark.integration)


@pytest.fixture(autouse=True)
def mock_validate_entitlement_key():
    """Mock validateEntitlementKey to always return True for integration tests.

    Integration tests focus on workflow and integration, not validation logic.
    Validation logic is covered by unit tests in test_entitlement_key_validation.py.
    """
    with mock.patch("mas.cli.cli.BaseApp.validateEntitlementKey", return_value=True):
        yield


# Made with Bob
