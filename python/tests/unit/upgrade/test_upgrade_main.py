# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for the upgrade command dispatch in __main__.py and UpgradeApp methods.

Covers: TUI path (no --mas-instance-id), non-interactive path (with --mas-instance-id),
and fetchInstalledInstanceIds caching and error behaviour.
"""

import pytest
from unittest.mock import MagicMock, patch

import mas.cli.__main__ as main_module
from mas.cli.upgrade.app import UpgradeApp

# ---------------------------------------------------------------------------
# main() dispatch
# ---------------------------------------------------------------------------


def test_main_upgrade_no_instance_calls_serve_tui_mode():
    """Test that main() routes to TUI mode when --mas-instance-id is omitted.

    GIVEN argv contains only 'mas-cli upgrade' (no --mas-instance-id)
    WHEN main() is called
    THEN serveTuiMode is called once with 'upgrade' as the first argument.
    """
    with (
        patch.object(main_module, "argv", ["mas-cli", "upgrade"]),
        patch.object(main_module, "serveTuiMode") as mockServeTui,
    ):
        main_module.main()

    mockServeTui.assert_called_once()
    call_args = mockServeTui.call_args
    assert call_args[0][0] == "upgrade"


def test_main_upgrade_with_instance_does_not_call_tui():
    """Test that main() bypasses TUI mode when --mas-instance-id is provided.

    GIVEN argv contains 'mas-cli upgrade --mas-instance-id inst1'
    WHEN main() is called
    THEN serveTuiMode is not called and UpgradeApp.upgrade is invoked.
    """
    mock_app = MagicMock()
    mock_app.upgrade.return_value = None
    mock_app_class = MagicMock(return_value=mock_app)

    with (
        patch.object(main_module, "argv", ["mas-cli", "upgrade", "--mas-instance-id", "inst1"]),
        patch.object(main_module, "serveTuiMode") as mockServeTui,
        patch("mas.cli.upgrade.app.UpgradeApp", mock_app_class),
    ):
        try:
            main_module.main()
        except SystemExit:
            pass

    mockServeTui.assert_not_called()
    mock_app.upgrade.assert_called_once()


# ---------------------------------------------------------------------------
# UpgradeApp.fetchInstalledInstanceIds
# ---------------------------------------------------------------------------


def test_fetch_installed_instance_ids_caches_sorted_list():
    """Test that fetchInstalledInstanceIds stores sorted IDs on the instance.

    GIVEN a connected dynamicClient returning two MAS Suite CRs
    WHEN fetchInstalledInstanceIds is called
    THEN _installedInstanceIds is set to a sorted list of instance ID strings.
    """
    app = UpgradeApp.__new__(UpgradeApp)

    suites = [
        {"metadata": {"labels": {"mas.ibm.com/instanceId": "prod"}}},
        {"metadata": {"labels": {"mas.ibm.com/instanceId": "dev"}}},
    ]
    with (
        patch.object(UpgradeApp, "dynamicClient", new_callable=lambda: property(lambda self: MagicMock())),
        patch("mas.cli.upgrade.app.listMasInstances", return_value=suites),
    ):
        app.fetchInstalledInstanceIds()

    assert app._installedInstanceIds == ["dev", "prod"]


def test_fetch_installed_instance_ids_raises_when_none_found():
    """Test that fetchInstalledInstanceIds raises RuntimeError when no MAS instances exist.

    GIVEN a connected dynamicClient returning an empty list
    WHEN fetchInstalledInstanceIds is called
    THEN RuntimeError is raised with a message about no instances found.
    """
    app = UpgradeApp.__new__(UpgradeApp)

    with (
        patch.object(UpgradeApp, "dynamicClient", new_callable=lambda: property(lambda self: MagicMock())),
        patch("mas.cli.upgrade.app.listMasInstances", return_value=[]),
    ):
        with pytest.raises(RuntimeError, match="No MAS instances were found"):
            app.fetchInstalledInstanceIds()
